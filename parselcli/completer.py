from prompt_toolkit.completion import Completion, WordCompleter

XPATH_COMPLETION = ['text()', 'contains(', 're:test(', 'following-sibling(', 'position()', 'last()']
CSS_COMPLETION = ['::text', '::attr(']
_FLAGS = ['strip', 'first', 'absolute', 'onlyfirst', 'join']
BASE_COMPLETION = ['css', 'xpath', '-help', '-debug']
for flag in _FLAGS:
    BASE_COMPLETION.extend(['+' + flag, '-' + flag])


def ends_with_part(word, text):
    for i in range(len(word)):
        if not word[:-i]:
            continue
        if text.endswith(word[:-i]):
            return word, len(word[:-i])


class MiddleWordCompleter(WordCompleter):
    def __init__(self, words, **kwargs):
        self.match_end = kwargs.pop('match_end', None)
        super().__init__(words, **kwargs)

    def get_completions(self, document, complete_event):
        # Get word/text before cursor.
        word_before_cursor = document.text_before_cursor
        if self.ignore_case:
            word_before_cursor = word_before_cursor.lower()

        def word_matches(word):
            """ True when the word before the cursor matches. """
            if self.ignore_case:
                word = word.lower()
            return ends_with_part(word, word_before_cursor)

        matches = [word_matches(a) for a in self.words]
        matches = [m for m in matches if m]
        matches = sorted(matches, key=lambda v: v[1], reverse=True)
        for m in matches:
            word, length = m
            display_meta = self.meta_dict.get(word, '')
            yield Completion(word, -length, display_meta=display_meta)
