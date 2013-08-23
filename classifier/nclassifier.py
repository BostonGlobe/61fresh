import nltk
import itertools
import sys
import random
import classifiedtweets
from nltk.probability import FreqDist, DictionaryProbDist, ELEProbDist, sum_logs
 
class Classifier(object):
    def __init__(self, training_set):
        self.training_set = training_set
        self.stopwords = nltk.corpus.stopwords.words("english")
        self.stemmer = nltk.PorterStemmer()
        self.minlength = 4
        self.maxlength = 25
         
    def text_process_entry(self, example):
        site_text = nltk.clean_html(example[0]).lower()
        original_tokens = itertools.chain.from_iterable(nltk.word_tokenize(w) for w in nltk.sent_tokenize(site_text))
        tokens = original_tokens 
        tokens = [w for w in tokens if not w in self.stopwords]
        tokens = [w for w in tokens if self.minlength < len(w) < self.maxlength]
        return (tokens, example[1])
 
    def text_process_all(self, exampleset):
        processed_training_set = [self.text_process_entry(i) for i in self.training_set]
        processed_training_set = filter(lambda x: len(x[0]) > 0, processed_training_set) 
        processed_texts = [i[0] for i in processed_training_set]
         
        all_words = nltk.FreqDist(itertools.chain.from_iterable(processed_texts))
        features_to_test = all_words.keys()[:5000]
        self.features_to_test = features_to_test
        featuresets = [(self.document_features(d), c) for (d,c) in processed_training_set]
        return featuresets
   
    '''
    build feature set
    ''' 
    def document_features(self, document):
        features = {}
        for word in self.features_to_test:
            features['contains(%s)' % word] = (word in document)
        return features

    '''
    build the NaiveBayesClassifier
    Test the Naive Bayes classifier
    classifier = nltk.NaiveBayesClassifier.train(train)
    ''' 
    def build_classifier(self, featuresets):
        random.shuffle(featuresets)
        len_featuresets = len(featuresets)
        cut_point = len(featuresets) / 5
        print "--------------------------"
        print cut_point
        print len_featuresets
        print "--------------------------"
        train_set, test_set = featuresets[cut_point:], featuresets[:cut_point]
        classifier = nltk.NaiveBayesClassifier.train(train_set)
        return (classifier, test_set)

    
    '''
    run the classifier, extract featuresets
    ''' 
    def run(self):
        featuresets = self.text_process_all(self.training_set)
        #print featuresets[0] 
        classifier, test_set = self.build_classifier(featuresets)
        self.classifier = classifier
        self.test_classifier(classifier, test_set)

    '''
    classify the text using max prob
    ''' 
    def classify(self, text):
        #return self.classifier.classify(self.document_features(text))
        probdist = self.classifier.prob_classify(self.document_features(text))
        return probdist.max()

    '''
    get the lables
    '''
    def labels(self):
        return self.classifier._labels

    '''
    get the label_probdist
    '''
    def label_probdist(self):
        return self.classifier._label_probdist

    '''
    get the feature prob dist
    '''
    def feature_probdist(self):
        return self.classifier._feature_probdist

    '''
    get the prob score
    '''
    def prob_classify(self, text):
        return self.classifier.prob_classify(self.document_features(text))

    '''
    this will return the max score
    '''
    def get_score(self, text):
        #return self.classifier.classify(self.document_features(text))
        probdist = self.classifier.prob_classify(self.document_features(text))
        return probdist.prob(probdist.max())

    '''
    this will return most informative features
    '''
    def test_classifier(self, classifier, test_set):
        print nltk.classify.accuracy(classifier, test_set)
        classifier.show_most_informative_features(40)

    '''
    Print Out the details
    '''
    def details(self,text):
        print "%s = classified as: %s" % (text, self.classifier.classify(self.document_features(text)))
        probdist = self.classifier.prob_classify(self.document_features(text))
        listofsamples = probdist.samples()
        print 'classified max %s ' % probdist.max()
        for m in range(len(listofsamples)):
            sampleitem = listofsamples[m]
            print "%s: %s" %  (sampleitem, probdist.prob(sampleitem))
            print "--------"
        
 
