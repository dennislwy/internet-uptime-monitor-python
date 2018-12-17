class NewOld(object):
    """
    New and old library
    """

    def __init__(self, value=None, onChangeCb=None, onUpdateCb=None):
        self._new = value
        self._old = value
        self._onChangeCb = onChangeCb
        self._onUpdateCb = onUpdateCb

    @property
    def Value(self):
        return self._new

    @Value.setter
    def Value(self, val):
        self._old = self._new
        self._new = val

        if self._onChangeCb is not None and self.Changed:
            self._onChangeCb(val)

        if self._onUpdateCb is not None:
            self._onUpdateCb(val)

    @property
    def New(self):
        return self._new

    @property
    def Old(self):
        return self._old

    @property
    def Changed(self):
        return self._old is not None and self._new != self._old

    #region event handlers

    @property
    def OnChange(self):
        return self._onChangeCb

    @OnChange.setter
    def OnChange(self, cb):
        self._onChangeCb = cb

    @property
    def OnUpdate(self):
        return self._onUpdateCb

    @OnUpdate.setter
    def OnUpdate(self, cb):
        self._onUpdateCb = cb

    #endregion
