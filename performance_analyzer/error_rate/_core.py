import string
from performance_analyzer.utils.string import StringUtil
from performance_analyzer.spellcheck import SpellChecker
from performance_analyzer.utils.session import SessionUtil
from performance_analyzer.utils.bounds import SANITY_BOUNDS
from lingua import Language, LanguageDetectorBuilder


languages = [Language.ENGLISH, Language.TURKISH]
detector = LanguageDetectorBuilder.from_languages(*languages).build()

class ErrorRateCalculator:
    """
    A class to calculate error rate metrics
    """

    def __init__(self, data_list:list, user_language:str):
        self.sessions = SessionUtil.split_into_sessions(data_list)
        self.data_list = data_list
        self.final_text = SessionUtil.get_final_text(self.data_list)
        self.initial_text = SessionUtil.get_initial_text(self.data_list)

        language = detector.detect_language_of(self.final_text)

        self._text_language = None
        if language == Language.ENGLISH:
            self._text_language = 'en'
        elif language == Language.TURKISH:
            self._text_language = 'tr'
        else:
            self._text_language = user_language

        self._original_words = []
        words = []
        if self.final_text.startswith(self.initial_text):
            words = self.final_text[len(self.initial_text):].split()
        else:
            words = self.final_text.split()

        self._original_words = [word.rstrip(string.punctuation) for word in words]

        self._corrected_words = []
        for word in self._original_words:
            spell_checker = SpellChecker()
            result = spell_checker.evaluate(word, self._text_language, 0)
            self._corrected_words.append(result)

    def kspc(self, additional_characters:int = 0) -> float:
        """
        KSPC (keystrokes per character) is the ratio of the total entered character count
        to the length of the transcribed string.

        :param additional_characters: additional characters deleted by user due to changing mind
        :return: calculated kspc value
        """
        session_size = len(self.data_list)
        transcribed_text_length = SessionUtil.get_overall_len(self.sessions) + additional_characters

        if transcribed_text_length == 0:
            # AWARE-fix (Option A): no transcribed characters -> KSPC is
            # undefined (0/0). Return NaN (invalid sentinel) instead of 0 so
            # downstream pipelines drop/impute it rather than reading "0 KSPC".
            return float("nan")

        kspc_value = session_size / transcribed_text_length

        # AWARE-fix: KSPC < 0.05 or > 20 indicates a snapshot/paste artefact,
        # not real typing efficiency. Return NaN (not 0) so it is explicitly
        # invalid downstream.
        lo, hi = SANITY_BOUNDS["kspc"]
        if kspc_value < lo or kspc_value > hi:
            return float("nan")

        return kspc_value

    def error_rate(self) -> float:
        """
        ER (error rate) is the ratio of incorrect characters to all characters entered.

        :return: calculated error rate
        """
        overall_diff = 0
        for i, word in enumerate(self._original_words):
            word = self._original_words[i]
            result = self._corrected_words[i]
            if not result.is_correct:
                if result.correct_text is None:
                    print('WARN:', word, 'is evaluated as', result.effective_rule, 'but could not offer a corrected text!')
                else:
                    overall_diff += StringUtil.string_distance(word, result.correct_text)

        text_length = SessionUtil.get_overall_len(self.sessions)

        if text_length == 0:
            return 0

        # AWARE-fix: use the session-aware denominator (already computed
        # above) instead of the raw final/initial delta, which can be
        # negative on backspace-heavy windows.
        return overall_diff / text_length

    def error_msd(self) -> float:
        """
        Minimum string distance (MSD) between intended and transcribed text.

        :return: msd between intended and transcribed text
        """
        overall_diff = 0
        for i, word in enumerate(self._original_words):
            word = self._original_words[i]
            result = self._corrected_words[i]
            if not result.is_correct:
                if result.correct_text is None:
                    print('WARN:', word, 'is evaluated as', result.effective_rule, 'but could not offer a corrected text!')
                else:
                    overall_diff += StringUtil.string_distance(word, result.correct_text)

        return overall_diff

    def text_language(self):
        return self._text_language

    def get_final_text(self):
        return self.final_text

