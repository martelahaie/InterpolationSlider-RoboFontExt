import ezui
import merz
from mojo.events import postEvent
from mojo.roboFont import AllFonts, CurrentGlyph, RGlyph
from mojo.subscriber import Subscriber, registerGlyphEditorSubscriber, registerSubscriberEvent, unregisterGlyphEditorSubscriber
from mojo.UI import inDarkMode    

"""
Interpolation Slider
by Andy Clymer, June 2018
"""

DEFAULT_KEY = "com.andyclymer.interpolationSlider"

class drawinterpolatedGlyph(Subscriber):

    debug = True
    controller = None

    def build(self):
        glyphEditor = self.getGlyphEditor()
        
        self.container = glyphEditor.extensionContainer(
            identifier=DEFAULT_KEY,
            location='background',
            clear=True
        )
        self.previewContainer = glyphEditor.extensionContainer(
            identifier=DEFAULT_KEY,
            location='preview',
            clear=True
        )
        self.referenceGlyphLayer = self.container.appendBaseSublayer()
        self.previewGlyphLayer = self.previewContainer.appendBaseSublayer()
        self.isPreview = False
        self.prevWidth = 0
        
    def destroy(self):
        self.container.clearSublayers()
        self.previewContainer.clearSublayers()

    def glyphUpdated(self):
        status = "❌"

        currentGlyph = CurrentGlyph()
        self.referenceGlyphLayer.setPosition((currentGlyph.width + 30, 0))
        self.referenceGlyphLayer.clearSublayers()
        self.previewGlyphLayer.setPosition((currentGlyph.width + 30, 0))
        self.previewGlyphLayer.clearSublayers()

        interpValue = self.controller.w.getItemValue("interpolationSlider")

        if currentGlyph.name in self.controller.source0 and currentGlyph.name in self.controller.source1:

            glyph0 = self.controller.source0[currentGlyph.name]
            glyph1 = self.controller.source1[currentGlyph.name]

            self.interpolatedGlyph = RGlyph()
            # Interpolate
            self.interpolatedGlyph.interpolate(interpValue, glyph0, glyph1)

            if glyph0 == glyph1:
                status = "⚪️"
            elif len(self.interpolatedGlyph.contours) > 0:
                status = "✅"
        
        self.controller.w.getItem("compatibilityText").set(f"Compatibility: {status}")

        if not status == "❌":
            if self.isPreview:
                self.drawPreviewGlyph()
            else:
                self.drawGlyph()

    def drawGlyph(self):
        # Draw the interpolated glyph outlines
        isDarkMode = inDarkMode()
        glyphLayer = self.referenceGlyphLayer.appendPathSublayer(
            fillColor=None,
            strokeColor=(isDarkMode, isDarkMode, isDarkMode, 1),
            strokeWidth=.5,
        )
        glyphPath = self.interpolatedGlyph.getRepresentation("merz.CGPath")
        glyphLayer.setPath(glyphPath)

        for contour in self.interpolatedGlyph.contours:
            for bPoint in contour.bPoints:
                inLoc = self.addPoints(bPoint.anchor, bPoint.bcpIn)
                outLoc = self.addPoints(bPoint.anchor, bPoint.bcpOut)

                self.referenceGlyphLayer.appendLineSublayer(
                   startPoint=inLoc,
                   endPoint=bPoint.anchor,
                   strokeWidth=.5,
                   strokeColor=(isDarkMode, isDarkMode, isDarkMode, 1),
                )
                self.referenceGlyphLayer.appendLineSublayer(
                   startPoint=bPoint.anchor,
                   endPoint=outLoc,
                   strokeWidth=.5,
                   strokeColor=(isDarkMode, isDarkMode, isDarkMode, 1),
                )
                self.referenceGlyphLayer.appendSymbolSublayer(
                    position=outLoc,
                    imageSettings=dict(
                        name="oval",
                        size=(5, 5),
                        fillColor=(not isDarkMode, not isDarkMode, not isDarkMode, 1),
                        strokeColor=(isDarkMode, isDarkMode, isDarkMode, 1),
                        strokeWidth=.5,
                    )
                )
                self.referenceGlyphLayer.appendSymbolSublayer(
                    position=inLoc,
                    imageSettings=dict(
                        name="oval",
                        size=(5, 5),
                        fillColor=(not isDarkMode, not isDarkMode, not isDarkMode, 1),
                        strokeColor=(isDarkMode, isDarkMode, isDarkMode, 1),
                        strokeWidth=.5,
                    )
                )
                self.referenceGlyphLayer.appendSymbolSublayer(
                    position=bPoint.anchor,
                    imageSettings=dict(
                        name="oval",
                        size=(5, 5),
                        fillColor=(not isDarkMode, not isDarkMode, not isDarkMode, 1),
                        strokeColor=(isDarkMode, isDarkMode, isDarkMode, 1),
                        strokeWidth=.5,
                    )
                )
 
    def drawPreviewGlyph(self):
        # Draw a filled in version of the interpolated glyph
        isDarkMode = inDarkMode()
        self.previewGlyphLayer.clearSublayers()
        glyphLayer = self.previewGlyphLayer.appendPathSublayer(
            fillColor=(isDarkMode, isDarkMode, isDarkMode, .4),
        )
        glyphPath = self.interpolatedGlyph.getRepresentation("merz.CGPath")
        glyphLayer.setPath(glyphPath)
    

    def addPoints(self, pt0, pt1):
        return (pt0[0] + pt1[0], pt0[1] + pt1[1])

    def interpolationSliderDidChange(self, info):
        self.glyphUpdated()
        
    def glyphEditorDidSetGlyph(self, info):
        self.glyphUpdated()
        
    def sharpToolDidChange(self, info):
        self.glyphUpdated()

    def glyphDidChange(self, info):
        self.glyphUpdated()

    def glyphEditorWillShowPreview(self, info):
        self.isPreview = True
        self.glyphUpdated()

    def glyphEditorWillHidePreview(self, info):
        self.isPreview = False
        self.glyphUpdated()

    def roboFontAppearanceChanged(self, info):
        self.glyphUpdated()


class InterpolationSliderInterface(Subscriber, ezui.WindowController):

    def build(self):
        content = """
        Sources:
        (This is a PopUpButton. ...) @firstSourceButton
        (This is a PopUpButton. ...) @secondSourceButton
        Compatibility: ⚪️   @compatibilityText
        ---
        --X-- @interpolationSlider
        """
        descriptionData = dict(
            content=dict(
                sizeStyle="small",
            ),
            firstSourceButton=dict(
                width=220,
                selected=0,
            ),
            secondSourceButton=dict(
                width=220,
                selected=1,
            ),
            compatibilityText=dict(
                alignment="right",
                width="fill",
            ),
            interpolationSlider=dict(
                minValue=0,
                value=0,
                maxValue=1,
            ),
        )
        self.w = ezui.EZPanel(
            title="Interpolation Slider",
            size=(200, "auto"),
            content=content,
            margins=10,
            descriptionData=descriptionData,
            controller=self
        )

    def started(self):
        self.w.open()

        self.collectFonts()
        self.optionsChanged()

        drawinterpolatedGlyph.controller = self
        registerGlyphEditorSubscriber(drawinterpolatedGlyph)

    def destroy(self):
        unregisterGlyphEditorSubscriber(drawinterpolatedGlyph)
        drawinterpolatedGlyph.controller = None

    def interpolationSliderCallback(self, sender):
        postEvent(eventName)

    def firstSourceButtonCallback(self, sender):
        self.optionsChanged()

    def secondSourceButtonCallback(self, sender):
        self.optionsChanged()

    def collectFonts(self):
        firstSourceButton = self.w.getItem("firstSourceButton")
        secondSourceButton = self.w.getItem("secondSourceButton")

        # Hold aside the current font choices
        font0idx = firstSourceButton.get()
        font1idx = secondSourceButton.get()
        if not font0idx == -1:
            font0name = self.fontNames[font0idx]
        else: font0name = None
        if not font1idx == -1:
            font1name = self.fontNames[font1idx]
        else: font1name = None

        # Collect info on all open fonts
        self.fonts = AllFonts()
        self.fontNames = []
        for font in self.fonts:
            self.fontNames.append(self.getFontName(font, self.fontNames))

        # Update the popUpButtons
        firstSourceButton.setItems(self.fontNames)
        secondSourceButton.setItems(self.fontNames)

        # If there weren't any previous names, try to set the first and second items in the list
        if font0name == None:
            if len(self.fonts):
                firstSourceButton.set(0)
        if font1name == None:
            if len(self.fonts)  >= 1:
                secondSourceButton.set(1)
        # Otherwise, if there had already been fonts choosen before new fonts were loaded,
        # try to set the index of the fonts that were already selected
        if font0name in self.fontNames:
            firstSourceButton.set(self.fontNames.index(font0name))
        if font1name in self.fontNames:
            secondSourceButton.set(self.fontNames.index(font1name))

    def getFontName(self, font, fonts):
        # A helper to get the font name, starting with the preferred name and working back to the PostScript name
        # Make sure that it's not the same name as another font in the fonts list
        if font.info.openTypeNamePreferredFamilyName and font.info.openTypeNamePreferredSubfamilyName:
            name = "%s %s" % (font.info.openTypeNamePreferredFamilyName, font.info.openTypeNamePreferredSubfamilyName)
        elif font.info.familyName and font.info.styleName:
            name = "%s %s" % (font.info.familyName, font.info.styleName)
        elif font.info.postscriptFullName:
            name = font.info.postscriptFullName
        elif font.info.postscriptFullName:
            name = font.info.postscriptFontName
        else: name = "Untitled"
        # Add a number to the name if this name already exists
        if name in fonts:
            i = 2
            while name + " (%s)" % i in fonts:
                i += 1
            name = name + " (%s)" % i
        return name

    def fontDocumentDidOpenNew(self, info):
        self.collectFonts()
        self.optionsChanged()

    def fontDocumentWillOpen(self, info):
        self.collectFonts()
        self.optionsChanged()

    def fontDocumentDidClose(self, info):
        self.collectFonts()
        self.optionsChanged()               
        
    def optionsChanged(self):
        firstSourceButton = self.w.getItem("firstSourceButton")
        secondSourceButton = self.w.getItem("secondSourceButton")

        source0idx = firstSourceButton.get()
        source1idx = secondSourceButton.get()

        if not source0idx == -1:
            self.source0 = self.fonts[source0idx]
            self.source1 = self.fonts[source1idx]

        postEvent(eventName)


eventName = f"{DEFAULT_KEY}.changed"

registerSubscriberEvent(
    subscriberEventName=eventName,
    methodName="interpolationSliderDidChange",
    lowLevelEventNames=[eventName],
    dispatcher="roboFont",
    documentation="Send when the Interpolation Slider did change parameters.",
    delay=0,
    debug=True
)

InterpolationSliderInterface()