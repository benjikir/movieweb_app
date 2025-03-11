from abc import ABC, abstractmethod

class DataManagerInterface(ABC):
    @abstractmethod
    def get_all_users(self):
        pass

    @abstractmethod
    def get_user_movies(self, user_id):
        pass


class InMemoryDataManager(DataManagerInterface):
    """
    A simple in-memory data manager using a dictionary.
    """

    def __init__(self, data):
        """
        Initializes the InMemoryDataManager with the given data.

        Args:
            data (dict): A dictionary where keys are user IDs and values
                         are lists of movie IDs.  Example:
                         {
                             1: [101, 102],
                             2: [201, 202, 203]
                         }
        """
        self.data = data

    def get_all_users(self):
        """
        Returns a list of all user IDs.
        """
        return list(self.data.keys())

    def get_user_movies(self, user_id):
        """
        Returns a list of movie IDs for a given user ID.

        Args:
            user_id (int): The ID of the user.

        Returns:
            list: A list of movie IDs, or an empty list if the user is not found.
        """
        return self.data.get(user_id, [])



