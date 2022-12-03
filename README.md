# GaribaldiPPP
Phenocam Image Pre-Processor for the Garibaldi Park Tundra Experiment
Also contains a suite of tools used for analyzing phenocam data - mainly tracking of image greenness over time.

avi-rip: multiprocessed script that does initial breakdown and organization of video frames
build_metadata: generates list of image objects for future ease of processing, uses OCR to retrieve date information and affiliate it with each image.

Dependencies:
* [scikit-video](http://www.scikit-video.org/stable/io.html)
* multiprocess
* opencv
* pytesseract

Requires FFMPEG and Tesseract to be installed.
