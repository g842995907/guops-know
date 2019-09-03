import re


class Validator:
    def __init__(self, parameter_dict):
        self.parameter_dict = parameter_dict
        self.is_valid = True

    def __required(self, parameter):
        if parameter not in self.parameter_dict:
            self.is_valid = False

    def __min_length(self, parameter, min_length):
        if len(self.parameter_dict[parameter]) < min_length:
            self.is_valid = False

    def __max_length(self, parameter, max_length):
        if len(self.parameter_dict[parameter]) > max_length:
            self.is_valid = False

    def __isdigit(self, parameter):
        if not self.parameter_dict[parameter].isdigit():
            self.is_valid = False

    def __min(self, parameter, min):
        if int(self.parameter_dict[parameter]) < min:
            self.is_valid = False

    def __max(self, parameter, max):
        if int(self.parameter_dict[parameter]) > max:
            self.is_valid = False

    def __regex(self, parameter, regex):
        if re.match(regex, self.parameter_dict[parameter]) is None:
            self.is_valid = False

    def __equal_to(self, parameter, equal_to):
        if self.parameter_dict[parameter] != self.parameter_dict[equal_to]:
            self.is_valid = False

    def __is_comma_separated_digit(self, parameter):
        for string in self.parameter_dict[parameter].split(','):
            if not string.isdigit():
                self.is_valid = False
                break

    def validate(self, parameter,
                 required=False, min_length=None,
                 max_length=None,
                 isdigit=False, min=None, max=None,
                 regex=None, equal_to=None,
                 is_comma_separated_digit=False):
        if required:
            if parameter in self.parameter_dict:
                if min_length is not None:
                    self.__min_length(parameter, min_length)
                if max_length is not None:
                    self.__max_length(parameter, max_length)
                if isdigit:
                    self.__isdigit(parameter)
                if min:
                    self.__min(parameter, min)
                if max:
                    self.__max(parameter, max)
                if regex is not None:
                    self.__regex(parameter, regex)
                if equal_to is not None:
                    self.__equal_to(parameter, equal_to)
                if is_comma_separated_digit:
                    self.__is_comma_separated_digit(parameter)
            else:
                self.is_valid = False

    def username(self):
        self.validate('username', required=True, regex=u'^[a-zA-Z0-9_\u4E00-\u9FA5]+$')

    def email(self):
        self.validate('email', required=True, regex=r'(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)')

    def teamName(self):
        self.validate('teamName', required=True, max_length=30)