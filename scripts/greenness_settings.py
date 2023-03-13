import types


class Setting:
    '''
    Convenient way to configure the greenness-extractor

    ```

    Attributes
    ----------
    methods : tuple of functions or function
        The extractor function to run on the images.
        Multiple functions passed as a tuple get run separately,
        resulting in multiple output files labelled with the provided labels
    do_quadrants : bool
        Whether or not to run extractor quadrants vs. the entire image
    labels : tuple of strings or string
        The label(s) to append to the start of each output csv
    all_images : bool
        whether or not to treat the image database as the newer
        version that uses all images in a day or the older one with just
        one image / day.
    percentile : int
        the percent of raw values to consider when generating a final result
        keeps the largest values 
    '''

    def __init__(self, methods, labels, do_quadrants, all_images=True, percentile=100):
        self.do_quadrants = do_quadrants
        if isinstance(methods, types.FunctionType):
            self.is_single = True
            self.methods = methods,
            self.labels = labels,
        else:
            self.methods = methods
            self.labels = labels
        self.percentile = percentile

        self.runs = zip(self.methods, self.labels)
