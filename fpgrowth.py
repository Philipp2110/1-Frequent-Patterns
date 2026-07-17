from typing import Set, List

from classes.dataset import Dataset
from classes.itemset import Itemset
from classes.item import Item
from classes.itemsets_with_occurrence_counts import ItemsetsWithOccurrenceCounts
from classes.sorted_dataset import SortedDataset
from classes.sorted_transaction import SortedTransaction
from classes.item_tuple import ItemTuple
from classes.fp_tree import FPTree
from classes.conditional_pattern_base import ConditionalPatternBase
from classes.conditional_pattern import ConditionalPattern


class FPgrowth:
    def __init__(self, min_support: int = 2):
        """
        Initialize the FP-growth algorithm with the a minimum (absolute) support.

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

    def _generate_frequent_one_itemsets_with_occurrence_counts(
        self, dataset: Dataset
    ) -> ItemsetsWithOccurrenceCounts:
        """
        Generate all frequent 1-itemsets for the given dataset.

        Parameters:
        dataset (Dataset): The dataset for which the frequent 1-itemsets should be generated.

        Returns:
        ItemsetsWithOccurrenceCounts: A dictionary containing the frequent 1-itemsets as keys and their occurrence counts as values.
        """
        item =[]
        sett = set()
        for d in dataset.transactions:
            for items in d.items:
                if (items.name in item):
                    continue
                item.append(items.name)
                sett.add(Itemset(frozenset({items})))
        
        dic = ItemsetsWithOccurrenceCounts(sett)
        for t in dataset.transactions:
            transactionlist = []
            for i in t.items:
                transactionlist.append(i.name)
            for s in sett:
                slist=[]
                for item in s:
                    slist.append(item.name)
                if(set(slist).issubset(set(transactionlist))):
                    dic.add_occurrence(s)
        temp = {}
        for s, anzahl in dic.items():
            if(anzahl >= self.min_support):
                temp[s] = anzahl
        count = ItemsetsWithOccurrenceCounts(temp)
        for c in temp:
            count.set_occurrence_count(c,temp[c])
        return count


    def _generate_f_list(
        self, frequent_one_itemsets: ItemsetsWithOccurrenceCounts
    ) -> List[Itemset]:
        """
        Generate the f-list for the given frequent 1-itemsets.

        Parameters:
        frequent_one_itemsets (ItemsetsWithOccurrenceCounts): The frequent 1-itemsets with their occurrence counts for which the F-list should be generated.

        Returns:
        List[Itemset]: A f-list containing the frequent 1-itemsets sorted by decreasing occurrence count.
        """
        ergebnis=[]
        dic ={}
        dic = dict(sorted(frequent_one_itemsets.items(), key = lambda item: item[1], reverse = True))
        for n in dic:
            ergebnis.append(n)
        return ergebnis


    def _sort_dataset_according_to_f_list(
        self, dataset: Dataset, f_list: List[Itemset]
    ) -> SortedDataset:
        """
        Sort the dataset according to the given f-list.

        Parameters:
        dataset (Dataset): The dataset to be sorted.
        f_list (List[Itemset]): The f-list according to which the dataset should be sorted.

        Returns:
        SortedDataset: The sorted dataset.
        """
        
        datasett = set()
        for t in dataset.transactions:
            sett = []
            for f in f_list:
                if f.items.issubset(t.items):
                    sett.append(list(f.items)[0])
            transaction = SortedTransaction(t.id, ItemTuple(tuple(sett)))
            datasett.add(transaction)
        return SortedDataset(frozenset(datasett))





    def _construct_initial_fp_tree(self, sorted_dataset: SortedDataset) -> FPTree:
        """
        Construct the initial FP-tree from the given sorted dataset.

        Parameters:
        sorted_dataset (SortedDataset): The sorted dataset from which the initial FP-tree should be constructed.

        Returns:
        FPTree: The initial FP-tree.
        """
        fp_tree = FPTree()
        for t in sorted_dataset.transactions:
            fp_tree.add_items_to_tree(t.items, 1)
        return fp_tree

    def _get_conditional_pattern_base(
        self, item: Item, fp_tree: FPTree
    ) -> ConditionalPatternBase:
        """
        Get the conditional pattern base for the given item in the FP-tree.

        Parameters:
        item (Item): The item for which the conditional pattern base should be generated.
        fp_tree (FPTree): The FP-tree from which the conditional pattern base should be extracted.

        Returns:
        ConditionalPatternBase: The conditional pattern base for the given item.
        """
        ergebnis=[]
        header_table= fp_tree.get_header_table()
        for e in header_table.elements:
            if(e.item == item):
                element = e
        
        for node in element.node_links:
            ergebnis.append(ConditionalPattern(ItemTuple(tuple(list(map(lambda x: x.item , node.get_predecessors())))), node.occurrence_count))
        return ConditionalPatternBase(frozenset(ergebnis))


    def _construct_conditional_fp_tree(
        self, conditional_pattern_base: ConditionalPatternBase
    ) -> FPTree:
        """
        Construct a conditional FP-tree from the given sorted dataset.

        Parameters:
        conditional_pattern_base (ConditionalPatternBase): The conditional pattern base for which the conditional FP-tree should be constructed.

        Returns:
        FPTree: The conditional FP-tree.
        """
        fp_tree = FPTree()
        for c in conditional_pattern_base.conditional_patterns:
            fp_tree.add_items_to_tree(c.prefix_items, c.occurrence_count)
        return fp_tree

    def fit(self, dataset: Dataset):
        """
        Use the FP-growth algorithm to find all frequent itemsets in the given dataset.
        Saves the frequent itemsets in the frequent_itemsets attribute.

        Parameters:
        dataset (Dataset): The dataset to which the FP-growth algorithm should be fitted.
        """
        def helper(self, fp: FPTree, bisherig: list[Item]):
            if(fp.is_empty()):
                return 
            header_table= fp.get_header_table()
            for node in header_table.elements:
                if(node.overall_occurrence_count>=self.min_support):
                    condi = self._get_conditional_pattern_base(node.item, fp)
                    weiter = bisherig.copy()
                    weiter.append(node.item)
                    self.frequent_itemsets.add(Itemset(frozenset(weiter)))
                    helper(self, self._construct_conditional_fp_tree(condi), weiter)
            return
        
        frequent = self._generate_frequent_one_itemsets_with_occurrence_counts(dataset)
        f_list = self._generate_f_list(frequent)
        sdata = self._sort_dataset_according_to_f_list(dataset, f_list)
        fftree = self._construct_initial_fp_tree(sdata)
        g =[]
        return helper(self, fftree, g)
        
    


        
