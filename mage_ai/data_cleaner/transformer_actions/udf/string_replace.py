from mage_ai.data_cleaner.transformer_actions.udf.base import BaseUDF


class StringReplace(BaseUDF):
    def execute(self):
        pattern = self.options.get('pattern')
        replacement = self.options.get('replacement')
        if pattern or replacement:
            return self.df[self.arguments[0]].str.replace(pattern, replacement)
        else:
            raise Exception('Require both `pattern` and `replacement` parameters.')
