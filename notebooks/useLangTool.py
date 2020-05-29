import os
import json
import pandas as pd
import language_check

from functools import wraps
import time
def timeit_wrapper(func):
    # https://martinheinz.dev/blog/13
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()  # Alternatively, you can use time.process_time()
        func_return_val = func(*args, **kwargs)
        end = time.perf_counter()
        print('{0:<10}.{1:<8} : {2:<8}'.format(func.__module__, func.__name__, end - start))
        return func_return_val, (end - start)
    return wrapper

@timeit_wrapper
def test_word(hobj, word):
    return 1, 2
    
ret, _ = test_word("", 'hydroxychloroquine')

tool = language_check.LanguageTool('en-US') # NLTK

def iterate_one(text, match):
    """
    Correct one amendment using first replacement suggestion.
    """
    rep = str(match.replacements)
    rep_len = len(rep)
    # print(text)
    # print(f'{"^".rjust(match.fromx + 1, " ")}')
    # print(f'{rep.rjust(match.fromx + rep_len, " ")}')
    try:
        if len(match.replacements) > 0:
            if match.replacements[0] != ".":
                return text[:match.fromx] + match.replacements[0] + text[match.tox:]
            else:
                return text
        else:
            return text
    except Exception as e:
        print(f"\n\n{text}\n{match.replacements}\n{match.fromx}\n{match.tox}\n{e}")
        
def one_row(arr_texts1, arr_texts, index=0):
    """
    Procee one sentence.
    """
    idx_sent = index
    text = arr_texts1[idx_sent]
    # text_ref = arr_texts[idx_sent]
    # print(f"{index}")
    # print(text)
    # print(text_ref)
    
    matches = tool.check(text)

    result = text
    for match in reversed(matches):
        result = iterate_one(result, match)
        
    return result.replace(" , ", ", ").replace(", ", " , ")

@timeit_wrapper
def batch_process(arr_texts1, arr_texts):
    """
    Process the whole datasets rows.
    """
    collection = []
    for idx, row in enumerate(arr_texts1):
        line = one_row(arr_texts1, arr_texts, idx)
        collection.append(line)
    return collection

@timeit_wrapper
def load_data(filepath="../../../../../_Foreign/jfleg/dev/", src="dev.src", ref="dev.ref0"):
    """
    Load text file into list of sentences.
    """
    # .ref* are corrected
    # .src contains errors
    # .spellchecked.src is spell checked with other errors
    arr_texts1 = []
    arr_texts = []
    with open(f"{filepath}{src}", mode="r", encoding="utf8") as f1:
        rawtext1 = f1.read()
        arr_texts1 = rawtext1.split("\n")

        with open(f"{filepath}{ref}", mode="r", encoding="utf8") as f:
            rawtext = f.read()
            arr_texts = rawtext.split("\n")
            # for idx, row in enumerate(arr_texts):
            #     print(f"{idx}\n{arr_texts1[idx]}\n{row}\n")
            
    return (arr_texts1, arr_texts)


def correct_sent(rawtext):
    """
    CoNLL-2014
    """
    arr_matches = rawtext.split("\nA ")
    original_sent = arr_matches[0][2:]
    if len(arr_matches) > 1:
        arr_sent = original_sent.split(" ")
        for item in reversed(arr_matches):
            arr_tmp = item.split(" ")
            if False:
                print(arr_tmp)
            if arr_tmp[0] != "S":
                idx = int(arr_tmp[0])
                # print("0   ", arr_tmp)
                arr_repl = ' '.join(arr_tmp[1:]).split("|||")
                idx2 = int(arr_repl[0])

                
                
                # Insert
                if idx == idx2:
                    if arr_repl[2] == "-NONE-":
                        arr_sent = arr_sent[:idx] + [""] + arr_sent[idx2:]
                    else:
                        # print("a   ", arr_repl[2])
                        arr_sent = arr_sent[:idx] + [arr_repl[2].split("||")[0]] + arr_sent[idx2:]
                elif idx + 1 == idx2:
                    if idx >= len(arr_sent):
                        arr_sent.append(".")
                    else:
                        if False:
                            print(idx)
                            print(arr_sent)
                            print(arr_sent[idx])
                            print(arr_repl)
                            print(arr_repl[2])
                            print()

                        # Replace
                        # No alternative correction
                        if arr_repl[len(arr_repl)-1] == "0":
                            if arr_repl[2] == "-NONE-":
                                arr_sent[idx] = ""
                            elif len(arr_repl[2].split("||")) > 1:
                                arr_sent[idx] = arr_repl[2].split("||")[0]
                            else:
                                arr_sent[idx] = arr_repl[2]
                else:
                    # idx2 is shifted by 2+
                    if idx >= len(arr_sent):
                        arr_sent.append(".")
                    else:
                        inserting_word = ""
                        if arr_repl[len(arr_repl)-1] == "0":
                            if arr_repl[2] == "-NONE-":
                                inserting_word = ""
                            elif len(arr_repl[2].split("||")) > 1:
                                inserting_word = arr_repl[2].split("||")[0]
                            else:
                                inserting_word = arr_repl[2]
                            # print(inserting_word)
                            arr_sent = arr_sent[:idx] + [inserting_word] + arr_sent[idx2:]

        return original_sent, ' '.join(arr_sent).replace("  ", " ").replace("  ", " ")
    else:
        return original_sent, original_sent
