import os
import pandas as pd
import re
import json
from const import NlpConst, varies, stoplist

### Content
# detect_lang
# prep_sentence
# PrepText

def load_tokens(filepath="./Jobs Schema - tokens.tsv"):
    """
    Load tokens for Extraction
    """
    df_token = pd.DataFrame()
    tokenfile = filepath
    if os.path.exists(tokenfile):
        df_token = pd.read_csv(tokenfile, sep="\t", encoding="utf8")
        print(list(df_token.columns))
        df_token = df_token[['Personality', 'Language', 'Qualification (academic)', 'Qualifiaction (professional)', 'Software', 'Programing Language', 'Soft Skill', 'Hard Skill', 'xxx']]
    return df_token

def get_levelobj(filepath="./Jobs Schema - level.tsv"):
    """
    Load tokens about Level
    """
    levelfile = filepath
    levelobj = {}
    if os.path.exists(levelfile):
        df_level = pd.read_csv(levelfile, sep="\t", encoding="utf8")
        # print(list(df_level.columns))
        # df_level = df_level[['Personality', 'Language', 'Qualification (academic)', 'Qualifiaction (professional)', 'Software', 'Programing Language', 'Soft Skill', 'Hard Skill', 'job experience time']]
        ajson = json.loads(df_level.to_json(orient='records'))

        
        for item in ajson:
            if item["level_for"] == "Language":
                levelobj[item["term"]] = item["value"]
    return levelobj

def do_field(df_token, field_select, job_req):
    token_list = list(set(df_token[~df_token[field_select].isnull()][field_select]))
    token_list = [x.replace("_", " ") for x in token_list]
    re_str = "[^a-z]({})[^a-z]".format("|".join(token_list)).replace("+", r"\+")
    # print(re_str)
    build_re = re.compile(re_str, re.IGNORECASE)
    # print(build_re)
    
    return build_re.findall(" {} ".format(str(job_req)))

def get_df(filepath="./jobsdb_dump_first100.json"):
    """
    (No Test)
    """
    df = {}
    if filepath.find(".jl") != -1:
        """
        For large json
        """
        JL = "./jobsdb_notcrawl_2019-12-12.jl"
        df = pd.read_json(JL, lines=True)
    else:
        """
        For small json (<10MB)
        """
        # df = pd.read_json(filepath, orient="records")
        with open("./jobsdb_dump_first100.json", mode='r', encoding='utf8') as f:
            ajson = json.loads(f.read())
            df = pd.DataFrame(ajson)
    return df

def prep_sentence(text):
    regex = re.compile(r"([^A-Z\s]{2})([A-Z])")
    new_text = regex.sub(r"\1.  \2", text)
    #new_text = new_text.replace("   ", ".   ").replace("  ", "   ").replace("  - ", ". ").replace(".. ", ". ")
    return new_text

def detect_lang(textbuffer):
    lang = "eng"
    detectlang = re.findall(r"[\u4e00-\u9fff]+", textbuffer)
    if len(detectlang) != 0:
        lang = "chi"

    return lang

def get_section_requirement(df, df_token):
    new_df = pd.DataFrame()
    idxSeries = []
    hasRequireSeries = []
    requirementSeries = []

    for idx in range(0, len(df["jobDetail"])):
        jam = JobAdsModel(df["jobDetail"][idx]["jobDescription"], df_token)
        jam.run_section()

        ##################
        text = df["jobDetail"][idx]["jobDescription"]
        # preprocess ()
        result = text.replace("&nbsp;", " ").replace("\xa0", " ")
        result = result.replace("&amp;", "&") # ＆
        result = result.replace("&quot;", "\"")

        result = result.strip("\n\r\t ")
        result = result.replace("\n\r", "\n").replace("\r\n", "\n")
        result = result.replace("\n\n", "\n").replace("\n", "  ")
        
        # remove HTML tag
        result = re.sub(r'\<.+?\>', ' ', result, flags=re.IGNORECASE)
        
        for item in varies:
            result = result.replace(item, " Requirements:  ")
        
        result = result.replace(" ", " ")
        result = result.replace("s (", "s:  (")
        result = result.replace("s:", "s: ")
        result = result.replace("s :", "s: ")
        result = result.replace(" :", ": ")
        result = result.replace("：", ": ")
        result = result.replace(": ", ":  ")
        result = result.replace("- ", "  -  ")

        text_pre0 = result

        # doing split_section()
        patt1 = re.compile("^(.*?) (Requirements?:?  .*)$")
        result1 = patt1.match("{}".format(str(text_pre0)))
        
        patt2 = {}
        result2 = {}
        
        # result is sections' array of different sections
        result = result1
        if result1 is None:
            # Capital "Requirement" could not be found, check lowercase
            patt2 = re.compile("^(.*?) (requirements?:?  .*)$", re.IGNORECASE)
            result2 = patt2.match("{}".format(str(text_pre0)))
            result = result2
            if result2 is None:
                # lowercase "requirement" also not found, use whole piece as sections' array
                result = [text_pre0]
        else:
            result = result1

        temp_sect = result
        sections = {}

        if temp_sect is not None:
            # print(temp_sect.group(0))
            # print("==================")
            # print(temp_sect.group(1))
            # print("==================")
            # print(temp_sect.group(2))
            sections = {
                "type": "group",
                "data": temp_sect
            }
        else:
            sections = {
                "type": "string",
                "data": text_pre0
            }
        ##################
        
        idxSeries.append(idx)
        
        print("\n\n")
        
        if sections["type"] == "group":
            print("### Has matches")
            print(sections["data"].group(2))
            hasRequireSeries.append(True)
            requirementSeries.append(sections["data"].group(2))
        else:
            print("=== No matches, Show Original")
            print(sections["data"])
            hasRequireSeries.append(False)
            requirementSeries.append(sections["data"])
            
    new_df["id"] = idxSeries
    new_df["hasReq"] = hasRequireSeries
    new_df["Req"] = requirementSeries
    #new_df.to_csv("09.req.csv", index=False, quoting=1, encoding="utf8")
    return new_df

def get_section_responsibility(df, df_token):
    new_df = pd.DataFrame()
    idxSeries = []
    hasWantedSeries = []
    rawSeries = []
    langSeries = []

    for idx in range(0, len(df["jobDetail"])):
        jd = df["jobDetail"][idx]["jobDescription"]

        jd = jd.replace("user requirement", "user require__ment")

        seq_num = 0
        seq_word = "equirement"

        req_pos = jd.find("equirement")
        res_pos = jd.find("esponsibilit")
        if req_pos < res_pos:
            seq_num = 1
            seq_word = "esponsibilit"
        else:
            if req_pos == -1:
                seq_num = 1
                seq_word = "esponsibilit"

        arr = jd.split(seq_word)
        text = ""
        if len(arr) > 1:
            text = arr[seq_num].replace("\xa0", " ").replace("\r\n", "\n\r").replace("\n\r", "\n").replace("\r", "\n")
            text = text.replace("\n\n", "\n").replace("\n\n", "\n").replace("\n\n", "\n")
            text = text.replace("\n", ". ")
            text = text.replace(".. ", ". ").replace(".. ", ". ").replace(".. ", ". ")
            hasWantedSeries.append(True)
        else:
            text = jd
            hasWantedSeries.append(False)

        idxSeries.append(idx)
        rawSeries.append(text)
        langSeries.append(detect_lang(text))
            
    new_df["id"] = idxSeries
    new_df["hasWant"] = hasWantedSeries
    new_df["raw"] = rawSeries
    new_df["lang"] = langSeries
    #new_df.to_csv("09.req.csv", index=False, quoting=1, encoding="utf8")
    return new_df


class JobExtractor2(NlpConst):
    text_raw = ""
    text_pre0 = ""
    text_pre = []
    df_token = {}
    lang_result = []
    all_result = {}
    
    def __init__(self, text, tokens):
        self.text_raw = text
        self.text_pre0 = self.preprocess(self.text_raw)
        self.df_token = tokens
    
    def preprocess(self, text):
        result = text.replace("&nbsp;", " ").replace("\xa0", " ")
        result = result.replace("&amp;", "&") # ＆
        result = result.replace("&quot;", "\"")

        result = result.strip("\n\r\t ")
        result = result.replace("\n\r", "\n").replace("\r\n", "\n")
        result = result.replace("\n\n", "\n").replace("\n", "  ")
        
        # remove HTML tag
        result = re.sub(r'\<.+?\>', ' ', result, flags=re.IGNORECASE)
        
        for item in varies:
            result = result.replace(item, " Requirements:  ")
        
        result = result.replace(" ", " ")
        result = result.replace("s (", "s:  (")
        result = result.replace("s:", "s: ")
        result = result.replace("s :", "s: ")
        result = result.replace(" :", ": ")
        result = result.replace("：", ": ")
        result = result.replace(": ", ":  ")
        result = result.replace("- ", "  -  ")
        
        return result

    def assign_text_pre(self, req):
        self.text_pre = req
    
    def split_section(self):
        patt1 = re.compile("^(.*?) (Requirements?:?  .*)$")
        result1 = patt1.match("{}".format(str(self.text_pre0)))
        
        patt2 = {}
        result2 = {}
        
        result = result1

        if result1 is None:
            patt2 = re.compile("^(.*?) (requirements?:?  .*)$", re.IGNORECASE)
            result2 = patt2.match("{}".format(str(self.text_pre0)))
            result = result2
            if result2 is None:
                self.text_pre = [self.text_pre0]
            else:
                self.text_pre = result2
            self.text_pre = [self.text_pre0]
        else:
            result = result1
            self.text_pre = result1
            
        return result
    
    def prep_sentence(self, text):
        regex = re.compile(r"([^A-Z\s]{2})([A-Z])")
        new_text = regex.sub(r"\1.  \2", text)
        new_text = new_text.replace("   ", ".   ").replace("  ", "   ").replace("  - ", ". ")
        return new_text
    
    def extract_tokens(self, section=1):
        self.lang_result = []
        self.all_result["token"] = {}
        for field_select in list(self.df_token.columns):
            result = do_field(self.df_token, field_select, self.text_pre[section])
            if field_select == "Language":
                self.lang_result = list(set(result))
            # print("{}: {}\n".format(field_select, list(set(result))))
            self.all_result["token"][field_select] = list(set(result))

    def process_exp_year(self, line) :
        l = []
        patt_str = r"(At least|Minimum)?\s?(.*year).*experience.*?(in)?(.*)[.;\n]"

        if line.lower().find("at least") != -1 or \
            line.lower().find("minimum") != -1:
            patt_str = r"((At least|Minimum)+?\s[^.]+?year.*?experience).*?(in)?(.*?)[.,;\n]"
        else:
            patt_str = r"(\s[^.]+?year.*?experience).*?(in)?(.*?)[.,;\n]"
        build_patt = re.compile(patt_str, re.IGNORECASE)
        ret = build_patt.findall(" {} ".format(line))
        result = []
        if len(ret) > 0:
            if len(ret[0]) > 0:
                result = ret[0][0]
        l = result
        return l

    def extract_exp_year(self, section=1):
        # Experience Time
        collection = []
        text = str(self.text_pre[section])
        text = text.replace("yrs ", "years ") + "."
        arr = self.prep_sentence(text).split('. ')

        for idx in range(len(arr)):
            line = arr[idx]

            inner_arr = line.split(';')
            if len(inner_arr) > 1:
                for inner_idx in range(len(inner_arr)):
                    inner_line = inner_arr[inner_idx]
                    l = self.process_exp_year(inner_line + ".")
                    if len(l) > 0:
                        collection.append(l)
            else:
                l = self.process_exp_year(line + ".")
                if len(l) > 0:
                    collection.append(l)

        self.all_result["exp_year"] = collection

    def process_exp_subject(self, line):
        l = []
        patt_str = ""
        if line.find("experience") != -1:
            if line.strip().find("  ") != -1:
                patt_str = r"(.+experience.+?(in|of|is|be)(.+?))\s\s\s?.+?[.;\n]"
            else:
                patt_str = r"(.+experience.+?(in|of|is|be)(.+?))[.;\n]"
            build_patt = re.compile(patt_str, re.IGNORECASE)
            ret = build_patt.findall(" {} ".format(line))
            result = []
            startInclude = False
            if len(ret) > 0:
                if len(ret[0]) > 0:
                    for idx in range(len(ret[0])):
                        if ret[0][idx] in ["in","of","is","be"]:
                            startInclude = True
                        if startInclude:
                            result.append(ret[0][idx])
            l = ' '.join(result)
        return l

    def extract_exp_subject(self, section=1):
        # Experience on Subject
        collection = []
        text = str(self.text_pre[section])
        arr = self.prep_sentence(text).split('. ')

        for idx in range(len(arr)):
            line = arr[idx]

            inner_arr = line.split(';')
            if len(inner_arr) > 1:
                for inner_idx in range(len(inner_arr)):
                    inner_line = inner_arr[inner_idx]
                    l = self.process_exp_subject(inner_line + ".")
                    if len(l) > 0:
                        collection.append(l)
            else:
                l = self.process_exp_subject(line + ".")
                if len(l) > 0:
                    collection.append(l)

        self.all_result["exp_subject"] = collection
    
    def extract_lang(self, section=1):
        self.all_result["lang"] = []
        levelobj = get_levelobj()
        for lang_patt_item in self.lang_result:
            level_patt = "|".join([x.replace("_", " ") for x in list(levelobj.keys())])
            patt_lang = r"[a-z\s]({}).*?({})".format(level_patt, lang_patt_item)

            build_patt_lang = re.compile(patt_lang, re.IGNORECASE)
            ret = build_patt_lang.findall(" {} ".format(str(self.text_pre[section])))
            # print("{}: {}\n".format("Lang", list(set(result_lang))))
            result = ' '.join(list(ret[0]))
            if len(ret) > 0:
                self.all_result["lang"].append(result)
        pass

    def output_df(self, extacted_json):
        new_obj = {}
        for key in extacted_json["token"]:
            new_obj[key] = ','.join(extacted_json["token"][key])
        new_obj["exp_year"] = ','.join(extacted_json["exp_year"])
        new_obj["exp_subject"] = ' '.join(extacted_json["exp_subject"])
        new_obj["lang"] = ','.join(extacted_json["lang"])
        new_obj
        return pd.DataFrame.from_dict([new_obj])

    def run(self, section=1):
        ### Run split_section to get requirement
        # self.split_section()

        if section < len(self.text_pre):
            process_section = section
        else:
            process_section = 0

        self.extract_tokens(section=process_section)
        self.extract_exp_year(section=process_section)
        self.extract_exp_subject(section=process_section)
        self.extract_lang(section=process_section)
        
        
        # TODO
        # Degree holder, qualified legal executive preferred but not a must

        # TODO
        # Good spoken English and Chinese language skills (fluency in Mandarin is an advantage)
        
        """
        def print_exp(i, line):
            asteral = ""
            if line.find("experience") != -1:
                asteral = "*"
            print("{}{}\t{}.".format(i, asteral, line.strip("\n\r\t ")))
        
        print("=== Original Start ===")
        gidx = 1
        arr = self.prep_sentence(self.text_pre[process_section]).split('. ')
        for idx in range(len(arr)):
            line = arr[idx]

            inner_arr = line.split(';')
            if len(inner_arr) > 1:
                for inner_idx in range(len(inner_arr)):
                    inner_line = inner_arr[inner_idx]
                    print_exp(gidx, inner_line)
                    gidx = gidx + 1
            else:
                print_exp(gidx, line)
                gidx = gidx + 1

        print("=== Original End ===")
        """

        return self.all_result

# @deprecated
class JobAdsModel():
    raw_html = "" # with html tags eg: <span>
    raw_text = "" # plain text
    
    nopunc_text = "" # remove punctuation
    lowercase_text = "" # normalize tokens
    nostopword_text = "" # for meaningful words
    
    sections = [] # from raw_text
    sentences = [] # from raw_text, using NLTK, Ckippar
    tokens = [] # from nostopword_text, find keywords by POS
    
    # By JobExtractor2
    length_by_char = -1 # from raw_text
    length_by_word = -1 # from nopunc_text
    length_by_sentence = -1 # from sentences
    
    je = {}
    df_token = {}

    def __init__(self, in_html, df_token):
        self.raw_html = in_html
        self.raw_text = self.raw_html
        self.df_token = df_token
        
    def run_section(self):
        self.je = JobExtractor2(self.raw_text, self.df_token)
        temp_sect = self.je.split_section()

        if temp_sect is not None:
            # print(temp_sect.group(0))
            # print("==================")
            # print(temp_sect.group(1))
            # print("==================")
            # print(temp_sect.group(2))
            self.sections = {
                "type": "group",
                "data": temp_sect
            }
        else:
            # print("Failed\n\n")
            # print(self.je.text_pre0)
            self.sections = {
                "type": "string",
                "data": self.je.text_pre0
            }


class PrepText(NlpConst):
    """
    # (01) raw input
    # (02) clean newline(\n\r), fill periods(".")

    # (03) sentence array

    # (04) from (02) => lower case
    # (05) from (04) => lower case, no punctuation

    raw_html = "" # with html tags eg: <span>
    raw_text = "" # plain text
    
    nopunc_text = "" # remove punctuation
    lowercase_text = "" # normalize tokens
    nostopword_text = "" # for meaningful words
    
    sections = [] # from raw_text
    sentences = [] # from raw_text, using NLTK, Ckippar
    tokens = [] # from nostopword_text, find keywords by POS

    # Usage:
    pt = PrepText(text)
    ajson = pt.get_variables()
    """
    raw_text = "" # (01)
    period_text = "" # (02)
    sentence_arr = [] # (03)
    lower_text = "" # (04)
    lower_text_nopunc = "" # (05)
    lang = "eng"

    def __init__(self, raw_text=""):
        self.sentence_arr = []
        self.set_raw_text(raw_text)
        self.set_lang()
        self.set_period_text()
        self.set_sentence_arr()
        self.set_lower_text()
        self.set_lower_text_nopunc()
        pass
    
    def _process_line(self, line, idx):
        self.sentence_arr.append(line)

    def get_instance(self):
        return self
    
    def set_lang(self):
        if len(self.raw_text) == 0:
            raise Exception("[Error]<set_lang>: Raw Text has 0 length.")

        self.lang = "eng"
        detectlang = re.findall(r"[\u4e00-\u9fff]+", self.raw_text)
        if len(detectlang) != 0:
            self.lang = "chi"

        return self
    
    def set_raw_text(self, raw_text):
        if len(raw_text) == 0:
            raise Exception("[Error]<set_raw_text>: Raw Text has 0 length.")
        self.raw_text = raw_text

        return self
    
    def set_period_text(self):
        """
        Known issues:
        1. (Over-killed proper nouns) JobsDB ==> Jobs.   DB
        2. 12/F ==> 12. /f
        """
        regex = re.compile(r"([^A-Z\s]{2})([A-Z])")
        new_text = regex.sub(r"\1.  \2", self.raw_text)
        new_text = new_text.replace("   ", ".   ").replace("  ", "   ").replace("  - ", ". ")
        new_text = new_text.replace("\xa0", " ").replace("\r\n", "\n\r").replace("\n\r", "\n").replace("\r", "\n")
        new_text = new_text.replace("\n\n", "\n").replace("\n\n", "\n").replace("\n\n", "\n")
        new_text = new_text.replace("\n", ". ")
        new_text = new_text.replace(".. ", ". ").replace(".. ", ". ").replace(".. ", ". ")
        self.period_text = new_text

        return self
    
    def set_sentence_arr(self):
        if len(self.period_text) == 0:
            raise Exception("[Error]<set_sentence_arr>: Period Text has 0 length.")

        gidx = 0
        arr = self.period_text.split('. ')
        for idx in range(len(arr)):
            line = arr[idx]

            inner_arr = line.split(';')
            if len(inner_arr) > 1:
                for inner_idx in range(len(inner_arr)):
                    inner_line = inner_arr[inner_idx]
                    self._process_line(inner_line, gidx)
                    gidx = gidx + 1
            else:
                self._process_line(line, gidx)
                gidx = gidx + 1

        return self
    
    def set_lower_text(self):
        if len(self.period_text) == 0:
            raise Exception("[Error]<set_lower_text>: Period Text has 0 length.")
        
        self.lower_text = self.period_text.lower()
        
        if self.lang != "eng":
            print("[Warn]<set_lower_text>: Contains non latin characters.")
        
        return self
    
    def set_lower_text_nopunc(self):
        if len(self.period_text) == 0:
            raise Exception("[Error]<set_lower_text_nopunc>: Period Text has 0 length.")
            
        x = self.lower_text
        new_text = re.sub(pattern=r'[\!"#$%&\*+,-./:;<=>?@^_`()|~=]', 
                        repl=' ', 
                        string=x
                       ).strip()
        self.lower_text_nopunc = new_text
        
        return self

    def remove_stop_word(self, text):
        stoplist = self.stoplist
        arr = text.split(' ')

        return self, ' '.join([x for x in arr if not x.lower() in stoplist])
    
    def get_variables(self):
        return {
            "raw_text": self.raw_text,
            "period_text": self.period_text,
            "sentence_arr": self.sentence_arr,
            "lower_text": self.lower_text,
            "lower_text_nopunc": self.lower_text_nopunc,
            "lang": self.lang,
        }

# End
