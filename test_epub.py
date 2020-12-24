import pandas as pd


def test_kjv_rows():
    kjv = pd.read_csv('Data/kjv.csv', sep='|', dtype={'chapter':str, 'verse':str})
    assert len(kjv.index) == 31102, "Should be 31102)"

def test_sv_rows():
    sv = pd.read_csv('Data/sv.csv', sep='|', dtype={'chapter':str, 'verse':str})
    assert len(sv.index) == 31175, "Should be 31175)"

def test_gbs_rows():
    gbs = pd.read_csv('Data/gbs.csv', sep='|', dtype={'chapter':str, 'verse':str})
    assert len(gbs.index) == 31173, "Should be 31173)"

def test_diff_sv_gbs():
    # read data
    sv = pd.read_csv('Data/sv.csv', sep='|', dtype={'chapter':str, 'verse':str})
    gbs = pd.read_csv('Data/gbs.csv', sep='|', dtype={'chapter':str, 'verse':str})

    # harmonize book names
    gbs.loc[gbs.book == 'Haggaï', 'book'] = 'Haggai'
    gbs.loc[gbs.book == 'Markus', 'book'] = 'Marcus'
    gbs.loc[gbs.book == '1 Korinthe', 'book'] = '1 Korinthiërs'
    gbs.loc[gbs.book == '2 Korinthe', 'book'] = '2 Korinthiërs'
    gbs.loc[gbs.book == 'Efeze', 'book'] = 'Efeziërs'
    gbs.loc[gbs.book == 'Filippenzen', 'book'] = 'Filippensen'
    gbs.loc[gbs.book == 'Kolossenzen', 'book'] = 'Kolossensen'
    gbs.loc[gbs.book == '1 Thessalonicenzen', 'book'] = '1 Thessalonicensen'
    gbs.loc[gbs.book == '2 Thessalonicenzen', 'book'] = '2 Thessalonicensen'

    # diff
    df = pd.merge(sv, gbs, how='outer', on=['book', 'chapter', 'verse'])
    diff = df[df.text_x.isna() | df.text_y.isna()]

    # test number of differences
    assert len(diff.index) == 2, "Should be 2)"

    # test exact differences
    assert list(diff[['book', 'chapter', 'verse']].iloc[0]) == ['Psalmen', '13', '7'], "Should be ['Psalmen', '13', '7']"
    assert list(diff[['book', 'chapter', 'verse']].iloc[1]) == ['Handelingen', '19', '41'], "Should be ['Handelingen', '19', '41']"

