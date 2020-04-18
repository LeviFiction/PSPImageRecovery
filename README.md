# PSPImageRecovery
A python script to recover PSPImage files if they become corrupted

# Introduction
This script attempts to provide a way to determine what kind of corrupted information exists inside of a PSPImage file that PaintShop Pro won't open.  It uses the last known file format guide provided by Corel on File Format Version 7.  Several major changes have occurred since that time and so even upon completion of the entire standard the file recovery options are not guaranteed to be complete.

## Current capabilities
Currently the script can read in a PSPImage file and report basic file information and layer names.  It will also attempt to export PNG copies of all raster layers for analysis.

## Current limitations
It only supports a tiny subset of all possible blocks, block types, and value evaluation.  It cannot restore or recover lost data.  And it cannot fix issues in files provided.

Does not provide a diagnostic output.

## To Dos
Allow for commandline parameters
Add default analysis functionality
Clean up code
Add support for more block types and information input

## Dependencies
* zlib
* math
* struct
* Pillow

## Installation
Currently it's not really an installed library or full program.  Simply put it into an environment with Pillow installed.
