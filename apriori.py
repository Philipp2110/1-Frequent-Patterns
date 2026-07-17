from typing import Set
from itertools import chain, combinations
from classes.dataset import Dataset
from classes.itemset import Itemset
from classes.itemsets_with_occurrence_counts import ItemsetsWithOccurrenceCounts


class Apriori:
    def __init__(self, min_support: int = 2):
        """
        Initialize the Apriori algorithm with the a minimum (absolute) support.

        Parameters:
        min_support (int): The minimum (absolute) support. This parameter defines the minimum number
                           of occurrences an itemset must have to be considered frequent. Must be a positive integer.
                           Default value is 2.
        """
        # Ensure that the minimum support is a positive integer
        if not isinstance(min_support, int) or min_support < 1:
            raise ValueError("The minimum support must be a positive integer.")

        self.min_support = min_support
        self.frequent_itemsets = set()

    def _generate_one_itemsets(self, dataset: Dataset) -> Set[Itemset]:
        """
        Generate all 1-itemsets for the given dataset.

        Parameters:
        dataset (Dataset): The dataset for which the 1-itemsets should be generated.

        Returns:
        Set[Itemset]: A set containing all 1-itemsets that are contained in the dataset.
        """
        item =[]
        sett = set()
        for d in dataset.transactions:
            for items in d.items:
                if (items.name in item):
                    continue
                item.append(items.name)
                sett.add(Itemset(frozenset({items})))
        
        return sett


    def _count_occurrences_of_itemsets(
        self, dataset: Dataset, itemsets: Set[Itemset]
    ) -> ItemsetsWithOccurrenceCounts:
        """
        Count the occurrences of the given itemsets in the dataset.

        Parameters:
        dataset (Dataset): The dataset for which the itemset occurrences should be counted.
        itemsets (Set[Itemset]): The itemsets for which the occurrences should be counted. The itemsets do not need to be present in the dataset.

        Returns:
        ItemsetsWithOccurrenceCounts: A dictionary containing the itemsets as keys and their occurrence counts as values.
        """
        dic = ItemsetsWithOccurrenceCounts(itemsets)
        for t in dataset.transactions:
            transactionlist = []
            for i in t.items:
                transactionlist.append(i.name)
            for s in itemsets:
                slist=[]
                for item in s:
                    slist.append(item.name)
                if(set(slist).issubset(set(transactionlist))):
                    dic.add_occurrence(s)

        return dic


    def _prune_itemsets_below_min_support(
        self,
        itemsets_with_occurrence_counts: ItemsetsWithOccurrenceCounts,
    ) -> Set[Itemset]:
        """
        Prune itemsets that are below the minimum support threshold.

        Parameters:
        itemsets_with_occurrence_counts (ItemsetsWithOccurrenceCounts): A dictionary containing the itemsets as keys and their occurrence counts as values.

        Returns:
        Set[Itemset]: A set containing all itemsets that are considered frequent.
        """
        sett = set()
        for i,c in itemsets_with_occurrence_counts.items():
            if(c>=self.min_support):
                sett.add(i)
            
        return sett


    def _generate_candidate_itemsets(
        self, frequent_itemsets: Set[Itemset]
    ) -> Set[Itemset]:
        """
        Generate length-k+1 candidate itemsets based on the given frequent itemsets. k is the length of the longest frequent itemset.

        Parameters:
        frequent_itemsets (Set[Itemset]): A set containing all frequent itemsets.

        Returns:
        Set[Itemset]: A set containing all length-k+1 candidate itemsets.
        """
        # If there are no frequent itemsets, return an empty set
        if not frequent_itemsets:
            return set()
        candidate =[]
        ergebnis= set()
        gueltige = []
        k = 0
        for itemset in frequent_itemsets:
            anzahl =0
            for i in itemset:
                anzahl+=1
            if(anzahl > k):
                k=anzahl
        for itemset in frequent_itemsets: 
            anzahl =0
            for i in itemset:
                anzahl+=1
            if(anzahl < k):
                continue
            for zweitesset in frequent_itemsets:
                if(len(zweitesset.items) !=k or zweitesset == itemset ):
                    continue
                for item in zweitesset.items:
                    copy = list(zweitesset.items.copy())
                    copy.remove(item)
                    if(set(copy).issubset(itemset.items)):
                        citemset=set(itemset.items.copy())
                        citemset.add(item)
                        candidate.append(citemset)

        gueltige= candidate.copy()
        for c in candidate:
            potenzmenge = chain.from_iterable(combinations(list(c), r) for r in range(len(list(c)) + 1))
            echtes_potenzmenge_set = {frozenset(d) for d in potenzmenge}
            for p in echtes_potenzmenge_set:
                if(len(p)==0 or len(p)==k+1):
                    continue
                if not Itemset(p) in frequent_itemsets:
                    gueltige.remove(c)
                    break
        for g in gueltige:
            ergebnis.add(Itemset(frozenset(g)))
        return ergebnis

    def fit(self, dataset: Dataset):
        """
        Use the Apriori algorithm to find all frequent itemsets in the given dataset.
        Saves the frequent itemsets in the frequent_itemsets attribute.

        Parameters:
        dataset (Dataset): The dataset to which the Apriori algorithm should be fitted.
        """
        # Reset the set of frequent itemsets
        self.frequent_itemsets = set()

        einzelElemente = self._generate_one_itemsets(dataset)
        frequent = self._prune_itemsets_below_min_support(self._count_occurrences_of_itemsets(dataset, einzelElemente))
        self.frequent_itemsets.update(frequent)
        frequent= self._generate_candidate_itemsets(self.frequent_itemsets)
        while(len(frequent)>0):
            candidates = self._generate_candidate_itemsets(self.frequent_itemsets)
            candidates = self._count_occurrences_of_itemsets(dataset, candidates)

            frequent = self._prune_itemsets_below_min_support(candidates)

            self.frequent_itemsets.update(frequent)
