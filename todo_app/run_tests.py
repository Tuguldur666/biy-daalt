"""
=============================================================================
  run_tests.py  —  Туршилтын Нарийвчилсан Тайлан
  Баг: III VI IX  |  Тугулдур · Билгүүн · Мөнхжин · Мөнхбат

  Windows:   python run_tests.py
  Linux/Mac: python3 run_tests.py
=============================================================================
"""

import unittest, sys, os, time, json, traceback

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tests.test_api import TestAuth, TestTasks, TestIsolation

def _enable_win_ansi():
    try:
        import ctypes
        k = ctypes.windll.kernel32
        k.SetConsoleMode(k.GetStdHandle(-11), 7)
        return True
    except Exception:
        return False

_has_color = sys.platform != 'win32' or _enable_win_ansi()
G  = '\033[92m' if _has_color else ''   # green
R  = '\033[91m' if _has_color else ''   # red
Y  = '\033[93m' if _has_color else ''   # yellow
C  = '\033[96m' if _has_color else ''   # cyan
B  = '\033[1m'  if _has_color else ''   # bold
RS = '\033[0m'  if _has_color else ''   # reset

W = 72

def sep(ch='═'): return ch * W


class _Result(unittest.TestResult):
    def __init__(self):
        super().__init__()
        self.records  = []   
        self._started = {}

    def startTest(self, test):
        super().startTest(test)
        self._started[id(test)] = time.perf_counter()

    def _ms(self, test):
        return (time.perf_counter() - self._started.get(id(test), time.perf_counter())) * 1000

    def addSuccess(self, test):
        super().addSuccess(test)
        self.records.append(('PASS',  test, self._ms(test), None))

    def addFailure(self, test, err):
        super().addFailure(test, err)
        self.records.append(('FAIL',  test, self._ms(test), err))

    def addError(self, test, err):
        super().addError(test, err)
        self.records.append(('ERROR', test, self._ms(test), err))

    def addSkip(self, test, reason):
        super().addSkip(test, reason)
        self.records.append(('SKIP',  test, self._ms(test), reason))


def run():
    print()
    print(B + C + sep() + RS)
    print(B + C + '  FLASK TO-DO API — ТУРШИЛТЫН ТАЙЛАН' + RS)
    print(B + C + '  Баг: III VI IX  |  Тугулдур · Билгүүн · Мөнхжин · Мөнхбат' + RS)
    print(B + C + '  Хэрэгсэл: Python unittest + Flask test client + SQLite' + RS)
    print(B + C + sep() + RS)
    print()

    suite  = unittest.TestSuite()
    loader = unittest.TestLoader()
    loader.sortTestMethodsUsing = None

    SECTIONS = [
        (TestAuth,      '🔐  AUTH — Бүртгэл & Нэвтрэлт (TC-001 ~ TC-007)'),
        (TestTasks,     '📋  TASKS — Даалгаврын CRUD (TC-008 ~ TC-017)'),
        (TestIsolation, '🛡   ISOLATION & SECURITY (TC-018 ~ TC-020)'),
    ]
    for cls, _ in SECTIONS:
        suite.addTests(loader.loadTestsFromTestCase(cls))

    result = _Result()
    t0 = time.perf_counter()
    suite.run(result)
    elapsed = time.perf_counter() - t0


    idx       = 0
    class_map = {cls.__name__: title for cls, title in SECTIONS}
    cur_cls   = None

    for status, test, ms, err in result.records:
        cname = test.__class__.__name__
        if cname != cur_cls:
            print()
            print(B + class_map.get(cname, cname) + RS)
            print(sep('─'))
            cur_cls = cname

        idx += 1
        badge = {
            'PASS':  G + ' [PASS] ' + RS,
            'FAIL':  R + ' [FAIL] ' + RS,
            'ERROR': R + '[ERROR] ' + RS,
            'SKIP':  Y + ' [SKIP] ' + RS,
        }[status]

        tc_id = f'TC-{idx:03d}'
        desc  = (test.shortDescription() or str(test))
        if ': ' in desc:
            desc = desc.split(': ', 1)[1]

        print(f'  {badge} {B}{tc_id}{RS}  {desc}  {C}({ms:.1f} ms){RS}')

        if err and status in ('FAIL', 'ERROR'):
            tb = traceback.format_exception(*err)
            for line in tb[-3:]:
                for ln in line.strip().splitlines():
                    print(f'           {R}{ln}{RS}')


    total   = len(result.records)
    passed  = sum(1 for s, *_ in result.records if s == 'PASS')
    failed  = sum(1 for s, *_ in result.records if s == 'FAIL')
    errors  = sum(1 for s, *_ in result.records if s == 'ERROR')
    skipped = sum(1 for s, *_ in result.records if s == 'SKIP')
    pct     = passed / total * 100 if total else 0.0

    print()
    print(B + sep() + RS)
    print(B + '  ХУРААНГУЙ ДҮН' + RS)
    print(sep('─'))

    rows = [
        ('Нийт тест',    B + str(total)   + RS,           ''),
        ('Тэнцсэн',      G + B + str(passed)  + RS,       '✅'),
        ('Унасан',       R + B + str(failed)  + RS,       '❌' if failed else ''),
        ('Алдаатай',     R + B + str(errors)  + RS,       '⚠️'  if errors else ''),
        ('Алгасагдсан',  Y + B + str(skipped) + RS,       ''),
        ('Тэнцэх хувь',  B + f'{pct:.1f}%' + RS,         ''),
        ('Нийт хугацаа', C + f'{elapsed:.3f} s' + RS,     ''),
    ]
    for label, value, icon in rows:
        print(f'  {label:<18}  {icon}  {value}')

    if failed or errors:
        print()
        print(R + B + '  ИЛЭРСЭН АЛДААНУУД (Bug Report):' + RS)
        print(sep('─'))
        bnum = 1
        for status, test, ms, err in result.records:
            if status in ('FAIL', 'ERROR'):
                desc = (test.shortDescription() or str(test))
                if ': ' in desc:
                    desc = desc.split(': ', 1)[1]
                print(f'  {R}BUG-{bnum:03d}{RS}  {desc}')
                bnum += 1


    print()
    if failed == 0 and errors == 0:
        print(G + B + '  ✅  БҮХ ТЕСТ ТЭНЦЛЭЭ — Систем ТОГТВОРТОЙ!' + RS)
    else:
        print(R + B + f'  ❌  {failed + errors} ТЕСТ УНАВ — Засварын шаардлагатай!' + RS)

    print(B + sep() + RS)
    print(f'  GitHub: https://github.com/Tuguldur666/biy-daalt')
    print(B + sep() + RS)
    print()

    return 0 if (failed == 0 and errors == 0) else 1


if __name__ == '__main__':
    sys.exit(run())
