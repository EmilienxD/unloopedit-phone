from typing import Generic, TypeVar, Iterator


T = TypeVar('T')


class iter_loop(Generic[T]):
    """
    An iterator class that loops through an iterable indefinitely.

    Attributes:
    ----------
        iterable (iterable): The iterable to loop through.
        iterator (iterator): The current iterator of the iterable.

    Methods:
    -------
        __iter__:
            Returns the iterator object itself.
        __next__:
            Returns the next item from the iterator, restarting from the beginning if needed.
        as_list:
            Returns the original iterable.
        __len__:
            Returns the length of the iterable.
    """

    def __init__(self, iterable: list[T]):
        """
        Initialize the iter_loop with the given iterable.

        Parameters:
        ----------
            iterable (iterable): The iterable to loop through.
        """
        self.iterable: list[T] = list(iterable)
        self.iterator: Iterator[T] = iter(self.iterable)

    def __iter__(self) -> Iterator[T]:
        """
        Return the iterator object itself.

        Returns:
        -------
            iter_loop: The iterator object itself.
        """
        return self.iterable

    def __next__(self) -> T:
        """
        Return the next item from the iterator, restarting from the beginning if needed.

        Returns:
        -------
            Any: The next item from the iterator.
        """
        if self.iterable:
            try:
                return next(self.iterator)
            except StopIteration:
                self.iterator = iter(self.iterable)
                return next(self.iterator)
        else:
            raise StopIteration('Can not get a next element from an empty iterator.')

    @property
    def as_list(self) -> list[T]:
        """
        Return the original iterable.

        Returns:
        -------
            iterable: The original iterable.
        """
        return self.iterable

    def __len__(self) -> int:
        """
        Return the length of the iterable.

        Returns:
        -------
            int: The length of the iterable.
        """
        return len(self.iterable)
    
    def __eq__(self, other: 'iter_loop') -> bool:
        return isinstance(other, self.__class__) and self.iterable == other.iterable
    
    def __repr__(self) -> str:
        """
        Represent the object as the original iterable.

        Returns:
        -------
            iterable: The original iterable.
        """
        return str(self.iterable)
    
    def __getitem__(self, index: int) -> T:
        """
        Return the element at the given index.

        Parameters:
        ----------
            index (int): The index of the element to return.
        """
        return self.iterable[index]
    
    def remove(self, element: T) -> None:
        """
        Remove an element from the list of iterable elements.

        Parameters:
        ----------
            element (Any): The element to remvove.
        """
        self.iterable.remove(element)

    def append(self, element: T) -> None:
        """
        Append an element to the end of the list of iterable elements.

        Parameters:
        ----------
            element (Any): The element to append.
        """
        self.iterable.append(element)

    def pop(self, index: int = -1) -> T:
        """
        Remove and return the element at the given index.
        If no index is specified, removes and returns the last item.

        Parameters:
        ----------
            index (int, optional): The index of the element to remove. Defaults to -1.

        Returns:
        -------
            Any: The removed element.
        """
        return self.iterable.pop(index)