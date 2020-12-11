import math
from scipy.stats import fisher_exact

def cca(freq_table):
    """
    Covarying Collexeme Analysis

    Parameters
    ----------
    freq_table : dict 
        A frequency table in the format of: 
            {
                (Slot1, Slot2): freq, 
                (Slot1, Slot2): freq, 
                ...
            }
        where Slot1 & Slot2 are lexical items in a same construction.

    Returns
    -------
    dict
        A dictionary with a pair of lexical items as keys and a dicionary of 
        association measures (returned by measure()) indicating the
        strength of attraction of the two lexical items.

    Notes
    -----
    The contingency table used in Covarying Collexeme Analysis:
                    L_slot1     ~L_slot1
        L_slot2       o11          o12
        ~L_slot2      o21          o22

    References:
        Desagulier, G. (2017). Corpus Linguistics and Statistics with R. p213-221.
    """

    # Get total size
    corp_size = sum(v for k, v in freq_table.items())
    
    # Get marginal sizes
    subj_totals = {}
    act_totals = {}
    for k, v in freq_table.items():
        subj, act = k
        if subj not in subj_totals: subj_totals[subj] = 0
        if act not in act_totals: act_totals[act] = 0
        subj_totals[subj] += v
        act_totals[act] += v
    
    # Compute collocation scores
    new_freq_table = {}
    for k, v in freq_table.items():
        subj, act = k
        subj_total, act_total = subj_totals[subj], act_totals[act]
        othersubj_total, otheract_total = corp_size - subj_total, corp_size - act_total
        
        # Compute observed frequencies
        o11 = v
        o12 = subj_total - o11
        o21 = act_total - o11
        o22 = othersubj_total - o21

        if o11 < 0 or o12 < 0 or o21 < 0 or o22 < 0:
            print(k)
            print(o11, o12, o21, o22)
            print(subj_total, act_total)
            raise Exception('negative freq')

        # Compute expected frequencies
        contingency_table = {
            'o11': o11,
            'o12': o12,
            'o21': o21,
            'o22': o22
        }
        new_freq_table[k] = measures(**contingency_table)
    
    return new_freq_table



def dca(freq_table):
    """
    Distinctive Collexeme Analysis

    Parameters
    ----------
    freq_table : dict 
        A frequency table in the format of: 
            {
                C1: {L1: freq, L2: freq, ...}, 
                C2: {L1: freq, L2: freq, ...}
            }
        where C1 & C2 are labels for construction types and 
        L1, L2, L3, ... are labels for word types.

    Returns
    -------
    dict
        A dictionary with lexical items as keys and a dicionary of 
        association measures (returned by measure()) indicating the
        strength of attraction of the lexical item to the two constructions.

    Notes
    -----
    The contingency table used in Distinctive Collexeme Analysis:
             Lj     ~Lj
        C1   o11    o12
        C2   o21    o22

    References:
        Desagulier, G. (2017). Corpus Linguistics and Statistics with R. p213-221.
    """
    cnst_keys = list(freq_table.keys())
    C1 = cnst_keys[0]
    C2 = cnst_keys[1]

    words = set()
    freq_totals = {}
    for key in cnst_keys:
        freq_totals[key] = 0
        for w in freq_table[key]:
            words.add(w)
            freq_totals[key] += freq_table[key][w]
    
    # Compute collocation measures
    scores = {}
    for w in words:
        a = freq_table[C1].get(w, 0)
        b = freq_totals[C1] - a
        c = freq_table[C2].get(w, 0)
        d = freq_totals[C2] - c
        try:
            scores[w] = measures(o11=a, o12=b, o21=c, o22=d)
        except:
            print(a, b, c, d)
    
    print(f'Pos: attract to {C1}\nNeg: attract to {C2}')
    return scores #{'scores': scores, 'pos': C1}



def measures(o11, o12, o21, o22):
    """Compute a list of association measures from the contingency table.

    Parameters
    ----------
    o11 : int
        Cell(1, 1) in a 2x2 contingency table.
    o12 : int
        Cell(1, 2) in a 2x2 contingency table.
    o21 : int
        Cell(2, 1) in a 2x2 contingency table.
    o22 : int
        Cell(2, 2) in a 2x2 contingency table.

    Returns
    -------
    dict
        A list of association strengths as measured by different stats.
        For Fisher's exact test, see scipy.stats.fisher_exact()

    Notes
    -----
    G2 stat significance levels: 3.8415 (p < 0.05); 10.8276 (p < 0.01)
    """

    o1_ = o11 + o12
    o2_ = o21 + o22
    o_1 = o11 + o21
    o_2 = o12 + o22
    _, fisher_exact_pvalue = fisher_exact([[o11, o12], [o21, o22]])
    fisher_attract = -math.log(fisher_exact_pvalue)

    total = o1_ + o2_
    e11 = o1_ * o_1 / total
    e12 = o1_ * o_2 / total
    e21 = o2_ * o_1 / total
    e22 = o2_ * o_2 / total
    
    # Compute G2
    if o11 == 0: o11 = 0.00000000001
    try:
        t11 = o11*math.log(o11/e11) if o11 != 0 else 0
        t12 = o12*math.log(o12/e12) if o12 != 0 else 0
        t21 = o21*math.log(o21/e21) if o21 != 0 else 0
        t22 = o22*math.log(o22/e22) if o22 != 0 else 0
    except:
        print(o11, o12, o21, o22, e11, e12, e21, e22)
        raise Exception('math error')
    G2 = 2 * (t11 + t12 + t21 + t22)
    if o11 < e11: 
        G2 = -G2
        fisher_attract = -fisher_attract

    return {
        'freq': o11,
        'fisher_exact': fisher_attract,
        "G2": G2,
        'MI': math.log2(o11/e11),
        'MI3': math.log2(o11 ** 3 / e11),
        'MI_logf': math.log2(o11/e11) * math.log(o11 + 1),
        't': (o11 - e11) / math.sqrt(e11),
        'Dice': 2 * e11 / (o1_ + o_1),
        "deltaP21": o11/o1_ - o21/o2_,
        "deltaP12": o11/o_1 - o21/o_2
    }



def rank_collo(collo_measures, sort_by='G2', reverse=True, freq_cutoff=1):
    """Helper function to sort the results of collostructional analyses as returned by dca() and cca().

    Parameters
    ----------
    collo_measures : dict
        The analysis results returned by dca() or cca()
    sort_by : str, optional
        The association measure used to sort the result, by default 'G2'. 
        See measure() for the list of possible assoiciation measures to use for sorting.
    reverse : bool, optional
        Whether to sort from high values to low ones, by default True
    freq_cutoff : int, optional
        The minimal number of occurrences required to be included in the
        results, by default 1

    Returns
    -------
    list
        A list of tuple of length three, with the second element being
        the association statistic used for sorting and the third element the frequency.
    """
    out = sorted( ((k, v[sort_by], v['freq']) for k, v in collo_measures.items() if v['freq'] >= freq_cutoff),
    key=lambda x: x[1], reverse=reverse)

    return out
