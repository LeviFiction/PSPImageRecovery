import struct
import zlib
import math
import sys
import os
from PIL import Image

#Define Global variables and data types

uncompressed_size = 0
size = (0,0)
buffer = None
Offset = 0
bufflen = 0

endian = "<"
BYTE = "B"  #8-bit unsigned int
B_ARRAY = "{}B" #8-bit unsigned int array
C_ARRAY = "{}b" #8-bit signed integer array (array of char)
DOUBLE = "d" #64-bit floating point value
DWORD = "I" #32-bit unsigned integer value
LONG = "i" #32-bit signed integer value
RECT = "4i" #Array of 4 longs ((x1,y1), (x2,y2))
RGBQUAD = "4B" #4 BYTE array (R,G,B,0)
WORD = "H" #16-bit unsigned integer value
COLOR = "3B" #array of 3 BYTES for True Color
PAL_COLOR = "B" #1 BYTE for color palette
    
File_Header = [endian+B_ARRAY.format(32), endian+WORD, endian+WORD]
GenImageAttr = None
ExtData_opt = None
TubeData_opt = None
CreatorData_opt = None
CompositeImage_opt = None
TableBank_opt = None
ColorPalette_pal = None
LayerBank = None
Selection_opt = None
AlphaBank_opt = None

FormatVersion = {
    3: "PSP 5 compatible Format",
    4: "PSP 6 compatible Format",
    5: "PSP 7 compatible Format",
    6: "PSP 8 compatible Format",
    7: "PSP 9 compatible Format",
    8: "PSP X compatible Format",
    9: "PSP X1 compatible Format",
    10: "PSP X2 compatible Format",
    11: "PSP X3 compatible Format",
    12: "PSP X4 - X7 compatible Format",
    13: "PSP X8 - 2020 compatible Format"
    }

PSPBlockID = ["PSP_IMAGE_BLOCK", # 0 - General Image Attributes Block (main)
    "PSP_CREATOR_BLOCK", # 1 - Creator Data Block (main)
    "PSP_COLOR_BLOCK", # 2 - Color Palette Block (main and sub)
    "PSP_LAYER_START_BLOCK", # 3 - Layer Bank Block (main)
    "PSP_LAYER_BLOCK", # 4 - Layer Block (sub)
    "PSP_CHANNEL_BLOCK", # 5 - Channel Block (sub)
    "PSP_SELECTION_BLOCK", # 6 - Selection Block (main)
    "PSP_ALPHA_BANK_BLOCK", # 7 - Alpha Bank Block (main)
    "PSP_ALPHA_CHANNEL_BLOCK",# 8 - Alpha Channel Block (sub)
    "PSP_COMPOSITE_IMAGE_BLOCK", # 9 = Composite Image Block (sub)
    "PSP_EXTENDED_DATA_BLOCK",# 10 - Extended Data Block (main)
    "PSP_TUBE_BLOCK", # 11 - Picture Tube Data Block (main)
    "PSP_ADJUSTMENT_EXTENSION_BLOCK", # 12 - Adjustment Layer Block (sub)
    "PSP_VECTOR_EXTENSION_BLOCK", # 13 - Vector Layer Block (sub)
    "PSP_SHAPE_BLOCK", # 14 - Vector Shape Block (sub)
    "PSP_PAINTSTYLE_BLOCK", # 15 - Paint Style Block (sub)
    "PSP_COMPOSITE_IMAGE_BANK_BLOCK", # 16 - Composite Image Bank (main)
    "PSP_COMPOSITE_ATTRIBUTES_BLOCK", # 17 - Composite Image Attr. (sub)
    "PSP_JPEG_BLOCK", # 18 - JPEG Image Block (sub)
    "PSP_LINESTYLE_BLOCK", # 19 - Line Style Block (sub)
    "PSP_TABLE_BANK_BLOCK", # 20 - Table Bank Block (main)
    "PSP_TABLE_BLOCK", # 21 - Table Block (sub)
    "PSP_PAPER_BLOCK", # 22 - Vector Table Paper Block (sub)
    "PSP_PATTERN_BLOCK", # 23 - Vector Table Pattern Block (sub)
    "PSP_GRADIENT_BLOCK", # 24 - Vector Table Gradient Block (not used)
    "PSP_GROUP_EXTENSION_BLOCK", # 25 - Group Layer Block (sub)
    "PSP_MASK_EXTENSION_BLOCK", # 26 - Mask Layer Block (sub)
    "PSP_BRUSH_BLOCK", # 27 - Brush Data Block (main)
    "PSP_ART_MEDIA_BLOCK", # 28 - Art Media Layer Block (main)
    "PSP_ART_MEDIA_MAP_BLOCK", # 29 - Art Media Layer map data Block (main)
    "PSP_ART_MEDIA_TILE_BLOCK", # 30 - Art Media Layer map tile Block(main)
    "PSP_ART_MEDIA_TEXTURE_BLOCK",# 31 - Art Media Layer map texture Block (main)
    "", #32 - Unknown block type and purpose 
    "PSP_LAYER_STYLE_BLOCK", # 33 - Layer Styles block (sub)
]

# Possible metrics used to measure resolution.

PSP_METRIC = [
    "PSP_METRIC_UNDEFINED", # Metric unknown
    "PSP_METRIC_INCH", # Resolution is in inches
    "PSP_METRIC_CM", # Resolution is in centimeters
    ]
    
#Creator application identifiers.

PSPCreatorAppID = [
    "PSP_CREATOR_APP_UNKNOWN", # Creator application unknown
    "PSP_CREATOR_APP_PAINT_SHOP_PRO", # Creator is Paint Shop Pro
    ]
    
# Creator field types.

PSPCreatorFieldID=[
    "PSP_CRTR_FLD_TITLE", # Image document title field
    "PSP_CRTR_FLD_CRT_DATE", # Creation date field
    "PSP_CRTR_FLD_MOD_DATE", # Modification date field
    "PSP_CRTR_FLD_ARTIST", # Artist name field
    "PSP_CRTR_FLD_CPYRGHT", # Copyright holder name field
    "PSP_CRTR_FLD_DESC", # Image document description field
    "PSP_CRTR_FLD_APP_ID", # Creating app id field
    "PSP_CRTR_FLD_APP_VER", # Creating app version field
    ]

# Extended data field types.

PSPExtendedDataID = [
    "PSP_XDATA_TRNS_INDEX", # Transparency index field
    "PSP_XDATA_GRID", # Image grid information
    "PSP_XDATA_GUIDE", # Image guide information
    "PSP_XDATA_EXIF", # Image EXIF information
    ]
    
#Grid units type.

PSPGridUnitsType = [
    "keGridUnitsPixels", # Grid units is pixels
    "keGridUnitsInches", # Grid units is inches
    "keGridUnitsCentimeters" # Grid units is centimeters
    ]
    
# Guide orientation type.

PSPGuideOrientationType = [
    "keHorizontalGuide", # Horizontal guide direction
    "keVerticalGuide" # Vertical guide direction
    ]

#Bitmap types.

PSPDIBType = [
    "PSP_DIB_IMAGE", # Layer color bitmap
    "PSP_DIB_TRANS_MASK", # Layer transparency mask bitmap
    "PSP_DIB_USER_MASK", # Layer user mask bitmap
    "PSP_DIB_SELECTION", # Selection mask bitmap
    "PSP_DIB_ALPHA_MASK", # Alpha channel mask bitmap
    "PSP_DIB_THUMBNAIL", # Thumbnail bitmap
    "PSP_DIB_THUMBNAIL_TRANS_MASK", # Thumbnail transparency mask
    "PSP_DIB_ADJUSTMENT_LAYER", # Adjustment layer bitmap
    "PSP_DIB_COMPOSITE", # Composite image bitmap
    "PSP_DIB_COMPOSITE_TRANS_MASK", # Composite image transparency
    "PSP_DIB_PAPER", # Paper bitmap
    "PSP_DIB_PATTERN", # Pattern bitmap
    "PSP_DIB_PATTERN_TRANS_MASK", # Pattern transparency mask
    ]
    
#Type of image in the composite image bank block.

PSPCompositeImageType=[
    "PSP_IMAGE_COMPOSITE", # Composite Image
    "PSP_IMAGE_THUMBNAIL", # Thumbnail Image
    ]
    
#Channel types.

PSPChannelType = [
    "PSP_CHANNEL_COMPOSITE", # Channel of single channel bitmap
    "PSP_CHANNEL_RED", # Red channel of 24-bit bitmap
    "PSP_CHANNEL_GREEN", # Green channel of 24-bit bitmap
    "PSP_CHANNEL_BLUE", # Blue channel of 24-bit bitmap
    ]

# Possible types of compression.

PSPCompression = [
    "PSP_COMP_NONE", # No compression
    "PSP_COMP_RLE", # RLE compression
    "PSP_COMP_LZ77", # LZ77 compression
    "PSP_COMP_JPEG" # JPEG compression (only used by thumbnail and composite image)
    ]
    
# Layer types.

PSPLayerType = [
    "keGLTUndefined", # Undefined layer type
    "keGLTRaster", # Standard raster layer
    "keGLTFloatingRasterSelection", # Floating selection (raster)
    "keGLTVector", # Vector layer
    "keGLTAdjustment", # Adjustment layer
    "keGLTGroup", # Group layer
    "keGLTMask", # Mask layer
    "keGLTArtMedia" # Art media layer
    ]
    
# Layer flags.

PSPLayerProperties = {
    0x00000001:"keVisibleFlag", # Layer is visible
    0x00000002:"keMaskPresenceFlag", # Layer has a mask
    }
    
# Blend modes.

PSPBlendModes = {
    0:"LAYER_BLEND_NORMAL",
    1:"LAYER_BLEND_DARKEN",
    2:"LAYER_BLEND_LIGHTEN",
    3:"LAYER_BLEND_LEGACY_HUE",
    4:"LAYER_BLEND_LEGACY_SATURATION",
    5:"LAYER_BLEND_LEGACY_COLOR",
    6:"LAYER_BLEND_LEGACY_LUMINOSITY",
    7:"LAYER_BLEND_MULTIPLY",
    8:"LAYER_BLEND_SCREEN",
    9:"LAYER_BLEND_DISSOLVE",
    10:"LAYER_BLEND_OVERLAY",
    11:"LAYER_BLEND_HARD_LIGHT",
    12:"LAYER_BLEND_SOFT_LIGHT",
    13:"LAYER_BLEND_DIFFERENCE",
    14:"LAYER_BLEND_DODGE",
    15:"LAYER_BLEND_BURN",
    16:"LAYER_BLEND_EXCLUSION",
    17:"LAYER_BLEND_TRUE_HUE",
    18:"LAYER_BLEND_TRUE_SATURATION",
    19:"LAYER_BLEND_TRUE_COLOR",
    20:"LAYER_BLEND_TRUE_LIGHTNESS",
    255:"LAYER_BLEND_ADJUST",
    }
    
# Adjustment layer types.

PSPAdjustmentLayerType = [
    "keAdjNone", # Undefined adjustment layer type
    "keAdjLevel", # Level adjustment
    "keAdjCurve", # Curve adjustment
    "keAdjBrightContrast", # Brightness-contrast adjustment
    "keAdjColorBal", # Color balance adjustment
    "keAdjHSL", # HSL adjustment
    "keAdjChannelMixer", # Channel mixer adjustment
    "keAdjInvert", # Invert adjustment
    "keAdjThreshold", # Threshold adjustment
    "keAdjPoster" # Posterize adjustment
    ]
    
# Art media layer map types

PSPArtMediaMapType = [
    "keArtMediaColorMap",
    "keArtMediaBumpMap",
    "keArtMediaShininessMap",
    "keArtMediaReflectivityMap",
    "keArtMediaDrynessMap"
    ]

# Vector shape types.

PSPVectorShapeType = [
    "keVSTUnknown", # Undefined vector type
    "keVSTText", # Shape represents lines of text
    "keVSTPolyline", # Shape represents a multiple segment line
    "keVSTEllipse", # Shape represents an ellipse (or circle)
    "keVSTPolygon", # Shape represents a closed polygon
    "keVSTGroup", # Shape represents a group shape
    ]

# Shape property flags

PSPShapeProperties = {
    0x00000001:"keShapeAntiAliased", # Shape is anti-aliased
    0x00000002:"keShapeSelected", # Shape is selected
    0x00000004:"keShapeVisible", # Shape is visible
    }
    
# Polyline node type flags.

PSPPolylineNodeTypes = {
    0x0000:"keNodeUnconstrained", # Default node type
    0x0001:"keNodeSmooth", # Node is smooth
    0x0002:"keNodeSymmetric", # Node is symmetric
    0x0004:"keNodeAligned", # Node is aligned
    0x0008:"keNodeActive", # Node is active
    0x0010:"keNodeLocked", # Node is locked
    0x0020:"keNodeSelected", # Node is selected
    0x0040:"keNodeVisible", # Node is visible
    0x0080:"keNodeClosed", # Node is closed
    }
    
# Paint style types.

PSPPaintStyleType = {
    0x0000:"keStyleNone", # No paint style info applies
    0x0001:"keStyleColor", # Color paint style info
    0x0002:"keStyleGradient", # Gradient paint style info
    0x0004:"keStylePattern", # Pattern paint style info
    0x0008:"keStylePaper", # Paper paint style info
    0x0010:"keStylePen", # Organic pen paint style info
    }

# Gradient type.

PSPStyleGradientType = [
    "keSGTLinear", # Linear gradient type
    "keSGTRadial", # Radial gradient type
    "keSGTRectangular", # Rectangulat gradient type
    "keSGTSunburst" # Sunburst gradient type
    ]
    
# Paint Style Cap Type (Start & End).

PSPStyleCapType = [
    "keSCTCapFlat", # Flat cap type (was round in psp6)
    "keSCTCapRound", # Round cap type (was square in psp6)
    "keSCTCapSquare", # Square cap type (was flat in psp6)
    "keSCTCapArrow", # Arrow cap type
    "keSCTCapCadArrow", # Cad arrow cap type
    "keSCTCapCurvedTipArrow", # Curved tip arrow cap type
    "keSCTCapRingBaseArrow", # Ring base arrow cap type
    "keSCTCapFluerDelis", # Fluer deLis cap type
    "keSCTCapFootball", # Football cap type
    "keSCTCapXr71Arrow", # Xr71 arrow cap type
    "keSCTCapLilly", # Lilly cap type
    "keSCTCapPinapple", # Pinapple cap type
    "keSCTCapBall", # Ball cap type
    "keSCTCapTulip" # Tulip cap type
    ]

# Paint Style Join Type.

PSPStyleJoinType = [
    "keSJTJoinMiter", # Miter join type
    "keSJTJoinRound", # Round join type
    "keSJTJoinBevel" # Bevel join type
    ]
    
# Organic pen type.

PSPStylePenType = [
    "keSPTOrganicPenNone", # Undefined pen type
    "keSPTOrganicPenMesh", # Mesh pen type
    "keSPTOrganicPenSand", # Sand pen type
    "keSPTOrganicPenCurlicues", # Curlicues pen type
    "keSPTOrganicPenRays", # Rays pen type
    "keSPTOrganicPenRipple", # Ripple pen type
    "keSPTOrganicPenWave", # Wave pen type
    "keSPTOrganicPen" # Generic pen type
    ]

# Text element types.

PSPTextElementType = [
    "keTextElemUnknown", # Undefined text element type
    "keTextElemChar", # A single character code
    "keTextElemCharStyle", # A character style change
    "keTextElemLineStyle" # A line style change
    ]

# Text alignment types.

PSPTextAlignment = [
    "keTextAlignmentLeft", # Left text alignment
    "keTextAlignmentCenter", # Center text alignment
    "keTextAlignmentRight" # Right text alignment
    ]

# Text antialias modes.

PSPAntialiasMode = [
    "keNoAntialias", # Antialias off
    "keSharpAntialias", # Sharp
    "keSmoothAntialias" # Smooth
    ]

# Text flow types

PSPTextFlow = [
    "keTFHorizontalDown", # Horizontal then down
    "keTFVerticalLeft", # Vertical then left
    "keTFVerticalRight", # Vertical then right
    "keTFHorizontalUp" # Horizontal then up
    ]
# Character style flags.

PSPCharacterProperties = {
    0x00000001:"keStyleItalic", # Italic property bit
    0x00000002:"keStyleStruck", # Strike-out property bit
    0x00000004:"keStyleUnderlined", # Underlined property bit
    0x00000008:"keStyleWarped", # Warped property bit
    0x00000010:"keStyleAntiAliased", # Anti-aliased property bit
    }

# Table type.

PSPTableType = [
    "keTTUndefined", # Undefined table type
    "keTTGradientTable", # Gradient table type
    "keTTPaperTable", # Paper table type
    "keTTPatternTable" # Pattern table type
    ]
    
# Picture tube placement mode.

TubePlacementMode = [
    "tpmRandom", # Place tube images in random intervals
    "tpmConstant", # Place tube images in constant intervals
    ]
    
# Picture tube selection mode.

TubeSelectionMode = [
    "tsmRandom", # Randomly select the next image in tube to display
    "tsmIncremental", # Select each tube image in turn
    "tsmAngular", # Select image based on cursor direction
    "tsmPressure", # Select image based on pressure (from pressure-sensitive pad)
    "tsmVelocity", # Select image based on cursor speed
    ]
    
# Graphic contents flags.

PSPGraphicContents = {
    # Layer types
    0x00000001:"keGCRasterLayers", # At least one raster layer
    0x00000002:"keGCVectorLayers", # At least one vector layer
    0x00000004:"keGCAdjustmentLayers", # At least one adjust. layer
    0x00000008:"keGCGroupLayers", # at least one group layer
    0x00000010:"keGCMaskLayers", # at least one mask layer
    0x00000020:"keGCArtMediaLayers", # at least one art media layer
    # Additional attributes
    0x00800000:"keGCMergedCache", # merged cache (composite image)
    0x01000000:"keGCThumbnail", # Has a thumbnail
    0x02000000:"keGCThumbnailTransparency", # Thumbnail transp.
    0x04000000:"keGCComposite", # Has a composite image
    0x08000000:"keGCCompositeTransparency", # Composite transp.
    0x10000000:"keGCFlatImage", # Just a background
    0x20000000:"keGCSelection", # Has a selection
    0x40000000:"keGCFloatingSelectionLayer", # Has float. selection
    0x80000000:"keGCAlphaChannels", # Has alpha channel(s)
    }
    
Block_Header = [B_ARRAY.format(4), WORD, DWORD]

def main():
    global bufflen
    # input("Getting Started")
    if len(sys.argv) < 2:
        print("No filename given")
        return
    Filename = sys.argv[1]
    if not os.path.isfile(Filename):
        print("Not a valid file, please try again")
        return
    try:
        with open(Filename, 'rb') as f:
            buffer = f.read()
        bufflen = len(buffer)
    except:
        print("Couldn't load file into memory")
        return
        
    h = FileHeader(buffer)
    if h.valid:
        offset = h.offset
        bufflen = len(buffer)
        while offset < bufflen:
            b = BLOCK(buffer,offset)
            if b.valid:
                if PSPBlockID[b.blockID] == "PSP_IMAGE_BLOCK":
                    ib = GENERAL_IMAGE_ATTRIBUTES(buffer,offset)
                    print("Expansionn field: " + str(not ib.size_test))
                    size = (ib.width,ib.height)
                    offset = ib.block_offset
                elif PSPBlockID[b.blockID] == "PSP_LAYER_START_BLOCK" and ib.valid:
                    if b.offset > bufflen:
                        print("Layer Bank is reporting itself as larger than the actual file") 
                    lb = LAYER_BANK(buffer,offset,ib.layercount, PSPCompression[ib.compression])
                    offset = lb.offset
                else:
                    offset = b.offset
                    
def grabData(offset, buffer, format):
    test = struct.calcsize(format)
    if offset+test > bufflen:
        print("{} Cannot return data at {} for {}".format(bufflen, offset, format))
    data = struct.unpack_from(format, buffer, offset)
    offset += struct.calcsize(format)
    return (offset, data)
    
class FileHeader():
    def __init__(this, buffer):
        opening_comp = (80, 97, 105, 110, 116, 32, 83, 104, 111, 112, 32, 80, 114, 111, 32, 73, 109, 97, 103, 101, 32, 70, 105, 108, 101, 10, 26, 0, 0, 0, 0, 0)
        offset = 0
        offset, data = grabData(offset, buffer, File_Header[0])
        if opening_comp == data:
            print("Valid file")
            offset, data = grabData(offset, buffer, File_Header[1])
            print(FormatVersion[data[0]])
            offset, minor = grabData(offset, buffer, File_Header[2])
            this.valid = 1
        else:
            print("Invalid File")
            this.valid = 0
        this.offset = offset

class GENERAL_IMAGE_ATTRIBUTES():
    def __init__(this, buffer, offset):
        HeaderIdentifier = (126,66,75,0)
        offset, data = grabData(offset, buffer, Block_Header[0])
        if HeaderIdentifier == data:
            this.valid = 1
            offset, data = grabData(offset, buffer, Block_Header[1])
            offset, data = grabData(offset, buffer, Block_Header[2])
            this.block_offset = offset + data[0]
            
            offset,data = grabData(offset, buffer, endian+DWORD)
            chunksize = data[0]
            offset,data = grabData(offset, buffer, endian+LONG)
            this.width = data[0]
            offset,data = grabData(offset, buffer, endian+LONG)
            this.height = data[0]
            offset,data = grabData(offset, buffer, endian+DOUBLE)
            this.resolution = data[0]
            offset,data = grabData(offset, buffer, endian+BYTE)
            this.metric = data[0]
            offset,data = grabData(offset, buffer, endian+WORD)
            this.compression = data[0]
            offset,data = grabData(offset, buffer, endian+WORD)
            this.bitdepth = data[0]
            offset,data = grabData(offset, buffer, endian+WORD)
            this.planecount = data[0]
            offset,data = grabData(offset, buffer, endian+DWORD)
            this.colorcount = data[0]
            offset,data = grabData(offset, buffer, endian+BYTE)
            this.greyscale = data[0]
            offset,data = grabData(offset, buffer, endian+DWORD)
            this.totalsize = data[0]
            offset,data = grabData(offset, buffer, endian+LONG)
            this.active_layer = data[0]
            offset,data = grabData(offset, buffer, endian+WORD)
            this.layercount = data[0]
            offset,data = grabData(offset, buffer, DWORD)
            this.graphic_contents = data[0]            
            print("Chunk Size: " + str(chunksize))
            print( "Width: " + str(this.width))
            print( "Height: " + str(this.height))
            print( "Resolution: " + str(this.resolution))
            print( "Metric: " + str(PSP_METRIC[ this.metric]))
            print( "Compression Type: " + str(PSPCompression[this.compression]))
            print( "Bit Depth: " + str(this.bitdepth))
            print( "Plane Count: " + str(this.planecount))
            print( "Color Count: " + str(this.colorcount))
            print( "Greyscale?: " + str(this.greyscale))
            print( "Total Image Size: " + str(this.totalsize))
            print( "Active Layer: " + str(this.active_layer))
            print( "Layer Count: " + str(this.layercount))
            for cont in PSPGraphicContents.keys():
                if cont & this.graphic_contents:
                    print("Graphic Contents: " + str(PSPGraphicContents[cont]))
            this.size_test = offset == this.block_offset
            this.offset = offset
        else:
            this.valid = 0
            
class BLOCK():
    def __init__(this, buffer, offset, printdata=False, printname=True):
        HeaderIdentifier = (126,66,75,0)
        offset, data = grabData(offset, buffer, Block_Header[0])
        if HeaderIdentifier == data:
            this.valid = 1
            offset, data = grabData(offset, buffer, Block_Header[1])
            if printdata:
                print(data)
            this.blockID = data[0]
            if printname:
                print(PSPBlockID[data[0]])
            offset, data = grabData(offset, buffer, Block_Header[2])
            this.offset = offset + data[0]
        else:
            this.valid = 0

class LAYER_BANK():
    def __init__(this, buffer, offset, layercount, comp_type='PSP_COMP_LZ77'):
        layers = []
        HeaderIdentifier = (126,66,75,0)
        offset, data = grabData(offset, buffer, Block_Header[0])
        if HeaderIdentifier == data:
            this.valid = 1
            offset, data = grabData(offset, buffer, Block_Header[1])
            this.blockID = data[0]
            #print PSPBlockID[data[0]]
            offset, data = grabData(offset, buffer, Block_Header[2])
            this.offset = offset + data[0]
            for index in range(layercount):
                tlb = LAYER_BLOCK(buffer,offset, comp_type)
                if tlb.valid:
                    offset = tlb.offset
                    layers.append(tlb)
                else:
                    print("Something went wrong")
                    break;
            
        else:
            this.valid = 0

class LAYER_BLOCK():
    def __init__(this, buffer, offset, comp_type='PSP_COMP_LZ77'):
        HeaderIdentifier = (126,66,75,0)
        offset, data = grabData(offset, buffer, Block_Header[0])
        if HeaderIdentifier == data:
            this.valid = 1
            offset, data = grabData(offset, buffer, Block_Header[1])
            this.blockID = data[0]
            #print PSPBlockID[data[0]]
            offset, data = grabData(offset, buffer, Block_Header[2])
            this.offset = offset + data[0]
            offset,data = grabData(offset, buffer, endian+DWORD)
            this.chunksize = data[0]
            offset,data = grabData(offset, buffer,  endian+WORD)
            offset,data = grabData(offset, buffer, endian+str(data[0])+"s")
            this.layername = data[0]
            offset, data = grabData(offset, buffer, endian+BYTE)
            this.type = data[0]
            offset,data = grabData(offset, buffer, endian+RECT)
            this.imagerect = data
            offset,data = grabData(offset, buffer, endian+RECT)
            this.layerrect = data
            offset, data = grabData(offset, buffer, endian+str(5)+BYTE)
            this.opacity = data[0]
            this.blendmode = PSPBlendModes[data[1]]
            this.flags = data[2]
            this.protectrans = data[3]
            this.linkgroup = data[4]
            offset,data = grabData(offset, buffer, endian+RECT)
            this.maskrect = data
            offset,data = grabData(offset, buffer, endian+RECT)
            this.savedmaskrect = data
            offset,data = grabData(offset, buffer, endian+B_ARRAY.format(3)+WORD)
            this.mask_linked, this.mask_disabled, this.mask_invert, this.range_count = data
            offset,data = grabData(offset, buffer, endian+B_ARRAY.format(4)*10)
            offset,data = grabData(offset, buffer, endian+BYTE+DWORD)
            print(this.layername)
            print("\t"+str(this.type))
            print("\t{} : {}".format(this.layername, this.imagerect[0:2]))
            #print(repr(buffer[offset:offset+4]))
            print("\t"+str(this.layerrect))
            #print("\t"+str(this.imagerect))
            print("\t"+str(this.opacity))
            print("\t"+str(this.blendmode))
            this.channels = []
            while offset < this.offset:
                b = BLOCK(buffer, offset,printname=True)
                if b.valid:
                    if PSPBlockID[b.blockID] == "PSP_CHANNEL_BLOCK":
                        b = CHANNEL_BLOCK(buffer, offset, comp_type)
                        this.channels.append(b)
                    elif PSPBlockID[b.blockID] == "PSP_LAYER_STYLE_BLOCK":
                        b = LAYER_STYLE_BLOCK(buffer,offset)
                    offset = b.offset
                    
                else:
                    offset = this.offset
            ssize = this.layerrect[2:]
            if this.channels:
                for chan in this.channels:
                    if len(chan.full) < ssize[0]*ssize[1]:
                        chan.full = chan.full + ((ssize[0]*ssize[1]) - len(chan.full))*b'\x00'
                    if chan.chan_type == "PSP_CHANNEL_RED":
                        print("Converting red channel and Removing Padding" if ssize[0]%4 != 0 else "Converting red channel")
                        #red = [x for x in chan.full]
                        r = Image.frombytes("L", ssize, removepadding(chan.full, ssize) if ssize[0]%4 != 0 else chan.full)
                        #a.save(this.layername+'.png')
                    elif chan.chan_type == "PSP_CHANNEL_GREEN":
                        print("Converting green channel")
                        g = Image.frombytes("L", ssize, removepadding(chan.full, ssize) if ssize[0]%4 != 0 else chan.full)
                        #a.save(this.layername+'.png')
                        #green = [x for x in chan.full]
                    elif chan.chan_type == "PSP_CHANNEL_BLUE":
                        print("Converting blue channel")
                        b = Image.frombytes("L", ssize, removepadding(chan.full, ssize) if ssize[0]%4 != 0 else chan.full)
                        #a.save(this.layername+'.png')
                        #blue = [x for x in chan.full]
                    elif chan.chan_type == "PSP_CHANNEL_COMPOSITE" and chan.bmp_type == "PSP_DIB_TRANS_MASK":
                        print("Converting transparent channel")
                        a = Image.frombytes("L", ssize, removepadding(chan.full, ssize) if ssize[0]%4 != 0 else chan.full)
                        #a.save(this.layername+'.png')
                        #alpha = [x for x in chan.full]
                if r and g and b and a:
                    RGBA = Image.merge("RGBA",(r,g,b,a))
                elif r and g and b:
                    RGBA = Image.merge("RGB",(r,g,b))
                if RGBA:
                    RGBA.save(this.layername+'({},{}).png'.format(*this.imagerect[0:2]))
                del(this.channels)
                #print("Zipping them up")
                #full = list(zip(red,green,blue))
                #del(red,green,blue)
                del(b)
        else:
            print("Not a valid layer")
            this.valid = 0
        
class EXTENDED_DATA_BLOCK():
    def __init__(this, buffer, offset):
        HeaderIdentifier = (126,66,75,0)
        offset, data = grabData(offset, buffer, Block_Header[0])
        if HeaderIdentifier == data:
            this.valid = 1
            offset, data = grabData(offset, buffer, Block_Header[1])
            this.blockID = data[0]
            print(PSPBlockID[data[0]])
            offset, data = grabData(offset, buffer, Block_Header[2])
            this.offset = offset + data[0]
        else:
            this.valid = 0

class LAYER_STYLE_BLOCK():
    def __init__(this, buffer, offset):
        HeaderIdentifier = (126,66,75,0)
        offset, data = grabData(offset, buffer, Block_Header[0])
        if HeaderIdentifier == data:
            this.valid = 1
            offset, data = grabData(offset, buffer, Block_Header[1])
            this.blockID = data[0]
            #print PSPBlockID[data[0]]
            offset, data = grabData(offset, buffer, Block_Header[2])
            this.offset = offset + data[0] + 8
        else:
            this.valid = 0
            
class CHANNEL_BLOCK():
    """This block contains an "unknown" expansion field option
    that needs to be accounted for. so near the bottom you'll see
    that I use totalsize - (chunk_size + comp_length)
    The channel block includes the total length of the block including 
    the chunk information header and the compressed data.  The chunk information
    header is always 16 bytes long.  Add this to the compresed data length
    And you know how long the block is without the unknown field.
    So if the total size is larger than the presumed size, that's how
    large the unknown field is.
    """
    def __init__(this, buffer, offset, comp_type = 'PSP_COMP_LZ77'):
        HeaderIdentifier = (126,66,75,0)
        offset, data = grabData(offset, buffer, Block_Header[0])
        if HeaderIdentifier == data:
            this.valid = 1
            offset, data = grabData(offset, buffer, Block_Header[1])
            this.blockID = data[0]
            #print PSPBlockID[data[0]]
            offset, data = grabData(offset, buffer, Block_Header[2])
            this.offset = offset + data[0]
            totalsize = data[0]
            offset, data = grabData(offset, buffer, endian+str(3)+DWORD+WORD+WORD)
            this.chunk_size = data[0]
            this.comp_length = data[1]
            this.uncomp_length = data[2]
            this.bmp_type = PSPDIBType[data[3]]
            this.chan_type = PSPChannelType[data[4]]
            offset = offset + (totalsize-(this.chunk_size + this.comp_length))
            this.channel = buffer[offset:offset+this.comp_length]
            # print("Channel length vs comp_length: ".format((offset))
            if comp_type == "PSP_COMP_LZ77":
                try:
                    # this.full = zlib.decompress(this.channel)
                    d = zlib.decompressobj()
                    this.full = d.decompress(this.channel)
                except:
                    print("\t\t\tFAILED TO UNPACK THIS CHANNEL")
            elif comp_type == "PSP_COMP_RLE":
                r = RLE()
                this.full = r.decompress(this.channel)
            print("\t\tBitmap Type:" + this.bmp_type + " : " + this.chan_type + " : {}:{}".format(this.uncomp_length, len(this.full)))
 
        else:
            this.valid = 0

class RLE():
    def __init__(this):
        pass
    def decompress(this, data):
        uncompressed = b''
        offset = 0
        while offset < len(data):
            b = data[offset]
            counter = struct.unpack("<B",b)[0]
            if  counter > 128:
                counter -= 128
                b = data[offset+1]
                uncompressed = uncompressed + counter * b
                offset += 2
            else:
                offset += 1
                uncompressed = uncompressed + data[offset:offset+counter]
                offset += counter
        return uncompressed
        
    def compress(this, data):
        #go through data until end, if next byte repeats 
        # compressed = b''
        # offset = 0
        # datalen = len(data)
        # while offset < datalen:
            # run = data[offset]
            # runoffset = offset
            # while runoffset+1 <= datalen and 
        pass

def removepadding(data,size):
    rowSize = int(math.ceil((8*size[0])/32)*4)
    byteSize = int(size[0])
    padding = rowSize - byteSize
    newdata = b''
    offset = 0
    datalen = len(data)
    lastPerc = 0
    print(size)
    print(rowSize)
    print(byteSize, padding)
    for y in range(size[1]):
        tmp = int(offset+byteSize)
        data = data[0:tmp] + data[tmp+padding:]
        perc = (((y*1.0)/size[1])*100)
        if perc >= lastPerc+10:
            print (((y*1.0)/size[1])*100)
            lastPerc = perc
    return data
    # while offset < datalen:
        # tmp = offset+byteSize
        # newdata += data[int(offset):int(tmp)]
        # offset += rowSize
    # return newdata
                    
if __name__ == "__main__":
    main()
