from typing import List, Dict
from performance_analyzer.utils.string import StringUtil

class SessionUtil:

    @staticmethod
    def split_into_sessions(data: List[Dict]) -> List[List[Dict]]:
        """
        Starts a new session when:
        - current item's before_text == ""
        - previous item's current_text != ""

        Returns:
            List of sessions (list of lists)
        """

        if not data:
            return []

        sessions = []
        current_session = [data[0]]

        for i in range(1, len(data)):
            prev_item = data[i - 1]
            current_item = data[i]

            # AWARE-fix: treat None like "" so missing before_text doesn't crash.
            cur_before = current_item.get("before_text") or ""
            prev_current = prev_item.get("current_text") or ""

            new_session = (
                    cur_before == ""
                    and StringUtil.remove_braces(prev_current) != ""
            )

            if new_session:
                sessions.append(current_session)
                current_session = [current_item]
            else:
                current_session.append(current_item)

        # Add last session
        if current_session:
            sessions.append(current_session)

        return sessions

    @staticmethod
    def get_final_text(data_list) -> str:
        # AWARE-fix: guard against empty list.
        if not data_list:
            return ""
        current_text = data_list[len(data_list) - 1].get('current_text') or ''
        return StringUtil.remove_braces(current_text)

    @staticmethod
    def get_initial_text(data_list) -> str:
        # AWARE-fix: empty-list guard + strip braces for symmetry with
        # get_final_text. Without this, a [-wrapped before_text would
        # make initial_text artificially longer than final_text.
        if not data_list:
            return ""
        before_text = data_list[0].get('before_text') or ''
        return StringUtil.remove_braces(before_text)

    @staticmethod
    def get_text_len(data_list) -> int:
        # AWARE-fix: clamp at 0. A session that net-shrinks (pure deletes
        # or backspacing past the initial text) contributes 0 "produced
        # characters", not a negative number. Without this clamp,
        # get_overall_len can go negative, producing negative KSPC.
        raw = len(SessionUtil.get_final_text(data_list)) - len(SessionUtil.get_initial_text(data_list))
        return max(0, raw)

    @staticmethod
    def get_overall_len(sessions: List[Dict]) -> int:
        text_length = 0
        for session in sessions:
            text_length += SessionUtil.get_text_len(session)
        return text_length
