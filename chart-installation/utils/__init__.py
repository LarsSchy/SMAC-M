class ExclusiveSet(set):
    """Debug class to exclude most layers from the mapfile"""
    def __contains__(self, item):
        return not super(ExclusiveSet, self).__contains__(item)
