import typing as ty
from copy import deepcopy


T = ty.TypeVar('T')


class UList(ty.Generic[T]):
    """
    A custom list class that ensures all elements are unique.

    Attributes:
    ----------
        _elements (list): The list of unique elements.
        _elements_set (set): A set of unique elements for fast membership testing.

    Methods:
    -------
    __init__:
        Initializes the UList with optional initial elements.
    append:
        Appends a unique element to the list.
    extend:
        Extends the list with unique elements from another list.
    remove:
        Removes an element from the list.
    copy:
        Create a copy of the list with unique elements.
    sort:
        Sort the unique elements.
    __repr__:
        Returns the string representation of the list.
    __str__:
        Returns the string representation of the list.
    __iter__:
        Returns an iterator over the list elements.
    __len__:
        Returns the number of elements in the list.
    __getitem__:
        Returns the element at the specified index.
    """
    def __init__(self, elements: ty.Iterable[T] | None = None):
        """
        Initializes the UList with optional initial elements.

        Parameters:s
        ----------
            elements (list): A list of initial elements.
        """
        self._elements_set: set[T] = set()
        self._elements: list[T] = []
        if elements:
            self.extend(elements)

    def append(self, element: T) -> None:
        """
        Appends a unique element to the list.

        Parameters:
        ----------
            element (T): The element to append.
        """
        if element not in self._elements_set:
            self._elements.append(element)
            self._elements_set.add(element)

    def extend(self, elements: ty.Iterable[T]) -> None:
        """
        Extends the list with unique elements from another list.

        Parameters:
        ----------
            elements (list): A list of elements to extend.
        """
        [self.append(element) for element in elements]

    def insert(self, index: int, element: T) -> None:
        """
        Inserts an element at a specific position.

        Parameters:
        ----------
            index (int): The index at which to insert the element.
            element (T): The element to insert.
        """
        if element not in self._elements_set:
            self._elements.insert(index, element)
            self._elements_set.add(element)

    def pop(self, index: int = -1) -> T:
        """
        Removes and returns the element at the specified index.
        """
        element = self._elements.pop(index)
        self._elements_set.remove(element)
        return element

    def remove(self, item: T) -> None:
        """
        Removes an element from the list.

        Parameters:
        ----------
            item (T): The element to remove.

        Raises:
        ------
            ValueError: If the element is not found in the list.
        """
        if item in self._elements_set:
            self._elements.remove(item)
            self._elements_set.remove(item)
        else:
            raise ValueError(f"{item} not in list")

    def deepcopy(self):
        """
        Create a copy of the list with unique elements.

        Returns:
        -------
            UList[T]: The new list with unique elements.
        """
        return deepcopy(self)
    
    def copy(self):
        """
        Create a copy of the list with unique elements.

        Returns:
        -------
            UList[T]: The new list with unique elements.
        """
        copy = self.__class__()
        copy._elements = self._elements.copy()
        copy._elements_set = self._elements_set.copy()
        return copy
    
    def update(self, elements: list[T]) -> None:
        for _element in reversed(self._elements):
            if _element in elements:
                self.remove(_element)
        self.extend(elements)

    def sort(self, key: ty.Callable[[T], ty.Any] = None, reverse: bool = False) -> None:
        """
        Sort the unique elements.

        Parameters:
        ----------
            key (Any): The sorting key.
            reverse (bool): Reverse the list after sorting.
        """
        self._elements.sort(key=key, reverse=reverse)
    
    def index(self, value: T, start: int = 0, end: int | None = None):
        if end is None:
            return self._elements.index(value, start)
        else:
            return self._elements.index(value, start, end)

    def filter(self, boolean_list: list[bool]) -> tuple['UList[T]', 'UList[T]']:
        elements_selected = self.copy()
        elements_not_selected = self.copy()
        for element, be in zip(self._elements, boolean_list):
            if bool(be):
                elements_not_selected.remove(element)
            else:
                elements_selected.remove(element)
        return elements_selected, elements_not_selected
    
    def __add__(self, other: 'UList[T]') -> 'UList[T]':
        """
        Returns a new UList containing the concatenation of self and other.

        Parameters:
        ----------
            other (UList[T]): The UList to concatenate with.

        Returns:
        -------
            UList[T]: A new UList containing elements from both lists.
        """
        result = self.copy()
        result.extend(other)
        return result

    def __repr__(self) -> str:
        """
        Returns the string representation of the list.

        Returns:
        -------
            str: The string representation of the list.
        """
        return repr(self._elements)

    def __str__(self) -> str:
        """
        Returns the string representation of the list.

        Returns:
        -------
            str: The string representation of the list.
        """
        return repr(self._elements)
    
    def __eq__(self, other: 'UList[T]') -> bool:
        return self._elements == other._elements

    def __iter__(self) -> ty.Iterator[T]:
        """
        Returns an iterator over the list elements.

        Returns:
        -------
            iterator: An iterator over the list elements.
        """
        return iter(self._elements)

    def __len__(self) -> int:
        """
        Returns the number of elements in the list.

        Returns:
        -------
            int: The number of elements in the list.
        """
        return len(self._elements)

    def __getitem__(self, index: int | slice):
        """
        Returns the element at the specified index.

        Parameters:
        ----------
            index (Any): The index of the element to retrieve.

        Returns:
        -------
            T: The element at the specified index.
        """
        if isinstance(index, slice):
            return self.__class__(self._elements[index])
        return self._elements[index]

    def __setitem__(self, index: int, value: T):
        self._elements_set.remove(self._elements[index])
        self._elements[index] = value
        self._elements_set.add(value)
        