from __future__ import print_function, unicode_literals
import random
import logging
import os

os.environ['NLTK_DATA'] = os.getcwd() + '/nltk_data'

from textblob import TextBlob
from config import FILTER_WORDS

logging.basicConfig()
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)



GREETING_KEYWORDS = ("hello", "hi", "greetings", "sup", "what's up",)

GREETING_RESPONSES = ["'sup bro", "hey", "*nods*", "hey you get my snap?"]

def check_for_greeting(sentence):
    """If any of the words in the user's input was a greeting, return a greeting response"""
    for word in sentence.words:
        if word.lower() in GREETING_KEYWORDS:
            return random.choice(GREETING_RESPONSES)


NONE_RESPONSES = [
    "uh whatever",
    "meet me at the foosball table, bro?",
    "code hard bro",
    "want to bro down and crush code?",
    "I'd like to add you to my professional network on LinkedIn",
    "Have you closed your seed round, dog?",
]




COMMENTS_ABOUT_SELF = [
    "You're just jealous",
    "I worked really hard on that",
    "My Klout score is {}".format(random.randint(100, 500)),
]



class UnacceptableUtteranceException(Exception):
    """Raise this (uncaught) exception if the response was going to trigger our blacklist"""
    pass


def starts_with_vowel(word):
    """Check for pronoun compability -- 'a' vs. 'an'"""
    return True if word[0] in 'aeiou' else False


def broback(sentence):
    """Main program loop: select a response for the input sentence and return it"""
    logger.info("Broback: respond to %s", sentence)
    resp = respond(sentence)
    return resp



def find_pronoun(sent):
    """Given a sentence, find a preferred pronoun to respond with. Returns None if no candidate
    pronoun is found in the input"""
    pronoun = None

    for word, part_of_speech in sent.pos_tags:

        if part_of_speech == 'PRP' and word.lower() == 'you':
            pronoun = 'I'
        elif part_of_speech == 'PRP' and word == 'I':

            pronoun = 'You'
    return pronoun


def find_verb(sent):
    """Pick a candidate verb for the sentence."""
    verb = None
    pos = None
    for word, part_of_speech in sent.pos_tags:
        if part_of_speech.startswith('VB'): 
            verb = word
            pos = part_of_speech
            break
    return verb, pos


def find_noun(sent):
    """Given a sentence, find the best candidate noun."""
    noun = None

    if not noun:
        for w, p in sent.pos_tags:
            if p == 'NN':  
                noun = w
                break
    if noun:
        logger.info("Found noun: %s", noun)

    return noun

def find_adjective(sent):
    """Given a sentence, find the best candidate adjective."""
    adj = None
    for w, p in sent.pos_tags:
        if p == 'JJ':  
            adj = w
            break
    return adj




def construct_response(pronoun, noun, verb):
    """No special cases matched, so we're going to try to construct a full sentence that uses as much
    of the user's input as possible"""
    resp = []

    if pronoun:
        resp.append(pronoun)

    if verb:
        verb_word = verb[0]
        if verb_word in ('be', 'am', 'is', "'m"):  
            if pronoun.lower() == 'you':

                resp.append("aren't really")
            else:
                resp.append(verb_word)
    if noun:
        pronoun = "an" if starts_with_vowel(noun) else "a"
        resp.append(pronoun + " " + noun)

    resp.append(random.choice(("tho", "bro", "lol", "bruh", "smh", "")))

    return " ".join(resp)




def check_for_comment_about_bot(pronoun, noun, adjective):
    """Check if the user's input was about the bot itself, in which case try to fashion a response
    that feels right based on their input. Returns the new best sentence, or None."""
    resp = None
    if pronoun == 'I' and (noun or adjective):
        if noun:
            if random.choice((True, False)):
                resp = random.choice(SELF_VERBS_WITH_NOUN_CAPS_PLURAL).format(**{'noun': noun.pluralize().capitalize()})
            else:
                resp = random.choice(SELF_VERBS_WITH_NOUN_LOWER).format(**{'noun': noun})
        else:
            resp = random.choice(SELF_VERBS_WITH_ADJECTIVE).format(**{'adjective': adjective})
    return resp


SELF_VERBS_WITH_NOUN_CAPS_PLURAL = [
    "My last startup totally crushed the {noun} vertical",
    "Were you aware I was a serial entrepreneur in the {noun} sector?",
    "My startup is Uber for {noun}",
    "I really consider myself an expert on {noun}",
]

SELF_VERBS_WITH_NOUN_LOWER = [
    "Yeah but I know a lot about {noun}",
    "My bros always ask me about {noun}",
]

SELF_VERBS_WITH_ADJECTIVE = [
    "I'm personally building the {adjective} Economy",
    "I consider myself to be a {adjective}preneur",
]


def preprocess_text(sentence):
    """Handle some weird edge cases in parsing, like 'i' needing to be capitalized
    to be correctly identified as a pronoun"""
    cleaned = []
    words = sentence.split(' ')
    for w in words:
        if w == 'i':
            w = 'I'
        if w == "i'm":
            w = "I'm"
        cleaned.append(w)

    return ' '.join(cleaned)


def respond(sentence):
    """Parse the user's inbound sentence and find candidate terms that make up a best-fit response"""
    cleaned = preprocess_text(sentence)
    parsed = TextBlob(cleaned)

   
    pronoun, noun, adjective, verb = find_candidate_parts_of_speech(parsed)

    
    resp = check_for_comment_about_bot(pronoun, noun, adjective)


    if not resp:
        resp = check_for_greeting(parsed)

    if not resp:

        if not pronoun:
            resp = random.choice(NONE_RESPONSES)
        elif pronoun == 'I' and not verb:
            resp = random.choice(COMMENTS_ABOUT_SELF)
        else:
            resp = construct_response(pronoun, noun, verb)


    if not resp:
        resp = random.choice(NONE_RESPONSES)

    logger.info("Returning phrase '%s'", resp)

    filter_response(resp)

    return resp

def find_candidate_parts_of_speech(parsed):
    """Given a parsed input, find the best pronoun, direct noun, adjective, and verb to match their input.
    Returns a tuple of pronoun, noun, adjective, verb any of which may be None if there was no good match"""
    pronoun = None
    noun = None
    adjective = None
    verb = None
    for sent in parsed.sentences:
        pronoun = find_pronoun(sent)
        noun = find_noun(sent)
        adjective = find_adjective(sent)
        verb = find_verb(sent)
    logger.info("Pronoun=%s, noun=%s, adjective=%s, verb=%s", pronoun, noun, adjective, verb)
    return pronoun, noun, adjective, verb





def filter_response(resp):
    """Don't allow any words to match our filter list"""
    tokenized = resp.split(' ')
    for word in tokenized:
        if '@' in word or '#' in word or '!' in word:
            raise UnacceptableUtteranceException()
        for s in FILTER_WORDS:
            if word.lower().startswith(s):
                raise UnacceptableUtteranceException()


if __name__ == '__main__':
    import sys


    if (len(sys.argv) > 0):
        saying = sys.argv[1]
    else:
        saying = "How are you, brobot?"
    print(broback(saying))
