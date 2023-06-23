from mage_ai.api.presenters.BasePresenter import BasePresenter


class FilePresenter(BasePresenter):
    default_attributes = [
        'children',
        'disabled',
        'name',
        'path',
    ]

    def present(self, **kwargs):
        return self.model if type(self.model) is dict else self.model.to_dict()
