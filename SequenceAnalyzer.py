import numpy as np
from typing import Tuple, Dict, Any
from ScoringSystem import ScoringSystem

'''
Author: Michal Martyniak (github: @micmarty)
Artur Śliwa (@asliwa)
Łukasz Reszetow (@lukaszreszetow)

Helpful resources: https://www.cs.cmu.edu/~ckingsf/bioinfo-lectures/local.pdf
Note: Smith Waterman and Needleman Wunsch algorithms are very, very similar but it's meant to be separated
'''


class SequencesAnalyzer:

    traceback_symbols = {
        0: '↖',
        1: '↑',
        2: '←',
        3: '•'
    }

    def __init__(self, seq_a: str, seq_b: str, load_csv: bool) -> None:
        self.seq_a = seq_a
        self.seq_b = seq_b

        self.scoring_sys = ScoringSystem(match=1, mismatch=-1, gap=-1)
        self.edit_cost_sys = ScoringSystem(match=0, mismatch=1, gap=1)

        if load_csv:
            self.scoring_sys.load_csv('scores.csv')
            self.edit_cost_sys.load_csv('edit_cost.csv')
            print('[Scoring system]\n', self.scoring_sys)
            print('[Edit cost system]\n', self.edit_cost_sys)

    def global_alignment(self) -> Tuple[str, str]:
        result = self.needleman_wunsch_algorithm(minimize=False, alignment_cal=True)
        alignment_a, alignment_b = self._tracebackGlobal(
            traceback_matrix=result['traceback_matrix'],
            start_pos=result['score_pos'])
        print()
        print('[Global Alignment] Score={}'.format(result['score']))
        print('Result:\n', result['result_matrix'])
        print('Traceback:\n', result['traceback_matrix'])
        print('Alignment:')
        print(alignment_a)
        print(alignment_b)
        return alignment_a, alignment_b

    def local_alignment(self) -> Tuple[str, str]:
        result = self.smith_waterman_algorithm()
        alignment_a, alignment_b = self._tracebackLocal(
            result_matrix=result['result_matrix'],
            traceback_matrix=result['traceback_matrix'],
            start_pos=result['score_pos'])
        print()
        print('Result:\n', result['result_matrix'])
        print('Traceback:\n', result['traceback_matrix'])
        print('[Local Alignment] Score={}'.format(result['score']))
        print('Alignment:')
        print(alignment_a)
        print(alignment_b)
        return alignment_a, alignment_b

    def similarity(self) -> int:
        result = self.needleman_wunsch_algorithm(minimize=False, alignment_cal=False)

        print(result['result_matrix'])
        print(result['traceback_matrix'])
        print('[Similarity] Score={}'.format(result['score']))
        return result['score']

    def edit_distance(self) -> int:
        result = self.needleman_wunsch_algorithm(minimize=True, alignment_cal=False)

        print(result['result_matrix'])
        print(result['traceback_matrix'])
        print('[Edit distance] Cost={}'.format(result['score']))
        return result['score']

    def needleman_wunsch_algorithm(self, minimize: bool, alignment_cal: bool) -> Dict[str, Any]:
        '''
        Dynamic programming technique
        Reference: [l3a.pdf, slide #5] + [https://en.wikipedia.org/wiki/Needleman–Wunsch_algorithm]
        Algorithm: Needleman-Wunch
        Time complexity: O(nm)
        Space complexity: O(nm)

        `minimize` is a flag which needs to be enabled when calculating edit distance
        '''
        # 1. Prepare dimensions (required additional 1 column and 1 row)
        rows, cols = len(self.seq_a) + 1, len(self.seq_b) + 1

        # 2. Initialize matrices
        # Use grid/matrix as graph-like acyclic digraph (array cells are vertices)
        H = np.zeros(shape=(rows, cols), dtype=int)
        traceback = np.zeros(shape=(rows, cols), dtype=np.dtype('U5'))

        if minimize:
            # Required for edit cost calculation
            score_func = self.edit_cost_sys.score
        else:
            # Required for similarity calculation
            score_func = self.scoring_sys.score

        if alignment_cal:
            # Required if global alignment is being calculated -> first rows and columns should have negative sign
            sign = -1
        else:
            # Required if similarity or edit cost is being calculated -> first rows and columns should be positive
            sign = 1

        # Put sequences' letters into first row and first column (better visualization)
        traceback[0, 1:] = np.array(list(self.seq_b), dtype=str)
        traceback[1:, 0] = np.array(list(self.seq_a), dtype=str)

        # 3. Top row and leftmost column, like: 0, 1, 2, 3, etc.
        H[0, :] = np.arange(start=0, stop=sign*cols, step=sign*1)
        H[:, 0] = np.arange(start=0, stop=sign*rows, step=sign*1)

        for row in range(1, rows):
            for col in range(1, cols):
                # Current pair of letters from sequence A and B
                a = self.seq_a[row - 1]
                b = self.seq_b[col - 1]

                leave_or_replace_letter = H[row - 1, col - 1] + score_func(a, b)
                delete_indel = H[row - 1, col] + score_func('-', b)
                insert_indel = H[row, col - 1] + score_func(a, '-')

                scores = [leave_or_replace_letter, delete_indel, insert_indel]

                if minimize:
                    best_action = np.argmin(scores)
                else:
                    best_action = np.argmax(scores)

                H[row, col] = scores[best_action]
                traceback[row, col] = self.traceback_symbols[best_action]

        return {
            'result_matrix': H,
            'traceback_matrix': traceback,
            'score': H[-1, -1],
            'score_pos': (rows - 1, cols - 1)
        }

    def smith_waterman_algorithm(self) -> Dict[str, Any]:
        # TODO Add description similar to needleman-wunsch
        # 1. Prepare dimensions (required additional 1 column and 1 row)
        rows, cols = len(self.seq_a) + 1, len(self.seq_b) + 1

        # 2. Initialize matrices
        # Use grid/matrix as graph-like acyclic digraph (array cells are vertices)
        H = np.zeros(shape=(rows, cols), dtype=int)
        traceback = np.zeros(shape=(rows, cols), dtype=np.dtype('U5'))

        # Put sequences' letters into first row and first column (better visualization)
        traceback[0, 1:] = np.array(list(self.seq_b), dtype=str)
        traceback[1:, 0] = np.array(list(self.seq_a), dtype=str)

        # 3. Top row and leftmost colum are already 0
        for row in range(1, rows):
            for col in range(1, cols):
                # Alias: current pair of letters
                a = self.seq_a[row - 1]
                b = self.seq_b[col - 1]

                score_func = self.scoring_sys.score
                leave_or_replace_letter = H[row - 1, col - 1] + score_func(a, b)
                delete_indel = H[row - 1, col] + score_func('-', b)
                insert_indel = H[row, col - 1] + score_func(a, '-')

                # Zero is required - ignore negative numbers
                scores = [leave_or_replace_letter,
                          delete_indel, insert_indel, 0]
                best_action = np.argmax(scores)

                H[row, col] = scores[best_action]
                traceback[row, col] = self.traceback_symbols[best_action]

        return {
            'result_matrix': H,
            'traceback_matrix': traceback,
            'score': H.max(),
            'score_pos': np.unravel_index(np.argmax(H, axis=None), H.shape)
        }

    def _tracebackLocal(self, result_matrix, traceback_matrix, start_pos: Tuple[int, int]) -> Tuple[str, str]:
        '''Use both matrices to replay the optimal route'''
        seq_a_aligned = ''
        seq_b_aligned = ''

        # 1. Select starting point
        position = list(start_pos)

        # 2. Terminate when 0 is reached (end of path)
        while result_matrix[position[0], position[1]] != 0:
            symbol = traceback_matrix[position[0], position[1]]
            letter_pair = self.translateArrow(symbol, position)
            seq_a_aligned += letter_pair[0]
            seq_b_aligned += letter_pair[1]
        # Reverse strings (traceback goes from bottom-right to top-left)
        return seq_a_aligned[::-1], seq_b_aligned[::-1]

    def _tracebackGlobal(self, traceback_matrix, start_pos: Tuple[int, int]) -> Tuple[str, str]:
        seq_a_aligned = ''
        seq_b_aligned = ''

        # 1. Select starting point
        position = list(start_pos)

        # 2. Terminate when top left corner (0,0) is reached (end of path)
        while all(x != 0 for x in position):
            symbol = traceback_matrix[position[0], position[1]]
            letter_pair = self.translateArrow(symbol, position)
            seq_a_aligned += letter_pair[0]
            seq_b_aligned += letter_pair[1]
        # Reverse strings (traceback goes from bottom-right to top-left)
        return seq_a_aligned[::-1], seq_b_aligned[::-1]

    def translateArrow(self, symbol, position) -> Tuple[str, str]:
        # Use arrows to navigate and collect letters (in reversed order)
        # Shift indexes by one (matrix has additional row and column)
        if symbol == '↖':
            position[0] -= 1
            position[1] -= 1
            return self.seq_a[position[0]], self.seq_b[position[1]]
        elif symbol == '↑':
            position[0] -= 1
            return self.seq_a[position[0]], '-'
        elif symbol == '←':
            position[1] -= 1
            return '-', self.seq_b[position[1]]
