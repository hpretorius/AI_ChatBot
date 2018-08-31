from unittest import TestCase
from chatterbot.conversation import Statement
from chatterbot.storage.sql_storage import SQLStorageAdapter


class SQLAlchemyAdapterTestCase(TestCase):

    @classmethod
    def setUpClass(cls):
        """
        Instantiate the adapter before any tests in the test case run.
        """
        cls.adapter = SQLStorageAdapter()

    def setUp(self):
        """
        Create the tables in the database before each test is run.
        """
        self.adapter.create()

    def tearDown(self):
        """
        Drop the tables in the database after each test is run.
        """
        self.adapter.drop()


class SQLStorageAdapterTestCase(SQLAlchemyAdapterTestCase):

    def test_get_latest_response_from_zero_responses(self):
        response = self.adapter.get_latest_response('test')

        self.assertIsNone(response)

    def test_get_latest_response_from_one_responses(self):
        conversation = 'test'
        statement_1 = Statement(text='A', conversation=conversation)
        statement_2 = Statement(text='B', conversation=conversation, in_response_to=statement_1.text)

        self.adapter.update(statement_1)
        self.adapter.update(statement_2)

        response = self.adapter.get_latest_response(conversation)

        self.assertEqual(statement_1, response)

    def test_get_latest_response_from_two_responses(self):
        conversation = 'test'
        statement_1 = Statement(text='A', conversation=conversation)
        statement_2 = Statement(text='B', conversation=conversation, in_response_to=statement_1.text)
        statement_3 = Statement(text='C', conversation=conversation, in_response_to=statement_2.text)

        self.adapter.update(statement_1)
        self.adapter.update(statement_2)
        self.adapter.update(statement_3)

        response = self.adapter.get_latest_response(conversation)

        self.assertEqual(statement_2, response)

    def test_get_latest_response_from_three_responses(self):
        conversation = 'test'
        statement_1 = Statement(text='A', conversation=conversation)
        statement_2 = Statement(text='B', conversation=conversation, in_response_to=statement_1.text)
        statement_3 = Statement(text='C', conversation=conversation, in_response_to=statement_2.text)
        statement_4 = Statement(text='D', conversation=conversation, in_response_to=statement_3.text)

        self.adapter.update(statement_1)
        self.adapter.update(statement_2)
        self.adapter.update(statement_3)
        self.adapter.update(statement_4)

        response = self.adapter.get_latest_response(conversation)

        self.assertEqual(statement_3, response)

    def test_set_database_uri_none(self):
        adapter = SQLStorageAdapter(database_uri=None)
        self.assertEqual(adapter.database_uri, 'sqlite://')

    def test_set_database_uri(self):
        adapter = SQLStorageAdapter(database_uri='sqlite:///db.sqlite3')
        self.assertEqual(adapter.database_uri, 'sqlite:///db.sqlite3')

    def test_count_returns_zero(self):
        """
        The count method should return a value of 0
        when nothing has been saved to the database.
        """
        self.assertEqual(self.adapter.count(), 0)

    def test_count_returns_value(self):
        """
        The count method should return a value of 1
        when one item has been saved to the database.
        """
        statement = Statement("Test statement")
        self.adapter.update(statement)
        self.assertEqual(self.adapter.count(), 1)

    def test_filter_text_statement_not_found(self):
        """
        Test that None is returned by the find method
        when a matching statement is not found.
        """
        self.assertEqual(len(self.adapter.filter(text="Non-existant")), 0)

    def test_filter_text_statement_found(self):
        """
        Test that a matching statement is returned
        when it exists in the database.
        """
        statement = Statement("New statement")
        self.adapter.update(statement)

        results = self.adapter.filter(text="New statement")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].text, statement.text)

    def test_update_adds_new_statement(self):
        statement = Statement("New statement")
        self.adapter.update(statement)

        results = self.adapter.filter(text="New statement")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].text, statement.text)

    def test_update_modifies_existing_statement(self):
        statement = Statement("New statement")
        self.adapter.update(statement)

        # Check the initial values
        results = self.adapter.filter(text=statement.text)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].in_response_to, None)

        # Update the statement value
        statement.in_response_to = "New response"
        self.adapter.update(statement)

        # Check that the values have changed
        results = self.adapter.filter(text=statement.text)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].in_response_to, "New response")

    def test_get_random_returns_statement(self):
        statement = Statement("New statement")
        self.adapter.update(statement)

        random_statement = self.adapter.get_random()
        self.assertEqual(random_statement.text, statement.text)

    def test_remove(self):
        text = "Sometimes you have to run before you can walk."
        statement = Statement(text)
        self.adapter.update(statement)
        self.adapter.remove(statement.text)
        results = self.adapter.filter(text=text)

        self.assertEqual(results, [])

    def test_get_response_statements(self):
        """
        Test that we are able to get a list of only statements
        that are known to be in response to another statement.
        """
        statement_list = [
            Statement("What... is your quest?"),
            Statement("This is a phone."),
            Statement("A what?", in_response_to="This is a phone."),
            Statement("A phone.", in_response_to="A what?")
        ]

        for statement in statement_list:
            self.adapter.update(statement)

        responses = self.adapter.get_response_statements()

        self.assertEqual(len(responses), 2)
        self.assertIn("This is a phone.", responses)
        self.assertIn("A what?", responses)


class SQLAlchemyStorageAdapterFilterTestCase(SQLAlchemyAdapterTestCase):

    def setUp(self):
        super(SQLAlchemyStorageAdapterFilterTestCase, self).setUp()

        self.statement1 = Statement(
            "Testing...",
            in_response_to="Why are you counting?"
        )
        self.statement2 = Statement(
            "Testing one, two, three.",
            in_response_to="Testing..."
        )

    def test_filter_text_no_matches(self):
        self.adapter.update(self.statement1)
        results = self.adapter.filter(text="Howdy")

        self.assertEqual(len(results), 0)

    def test_filter_in_response_to_no_matches(self):
        self.adapter.update(self.statement1)

        results = self.adapter.filter(in_response_to="Maybe")
        self.assertEqual(len(results), 0)

    def test_filter_equal_results(self):
        statement1 = Statement(
            "Testing...",
            in_response_to=None
        )
        statement2 = Statement(
            "Testing one, two, three.",
            in_response_to=None
        )
        self.adapter.update(statement1)
        self.adapter.update(statement2)

        results = self.adapter.filter(in_response_to=None)
        self.assertEqual(len(results), 2)
        self.assertIn(statement1, results)
        self.assertIn(statement2, results)

    def test_filter_no_parameters(self):
        """
        If no parameters are passed to the filter,
        then all statements should be returned.
        """
        statement1 = Statement("Testing...")
        statement2 = Statement("Testing one, two, three.")
        self.adapter.update(statement1)
        self.adapter.update(statement2)

        results = self.adapter.filter()

        self.assertEqual(len(results), 2)

    def test_response_list_in_results(self):
        """
        If a statement with response values is found using
        the filter method, they should be returned as
        response objects.
        """
        statement = Statement(
            "The first is to help yourself, the second is to help others.",
            in_response_to="Why do people have two hands?"
        )
        self.adapter.update(statement)
        found = self.adapter.filter(text=statement.text)

        self.assertEqual(found[0].in_response_to, statement.in_response_to)


class ReadOnlySQLStorageAdapterTestCase(SQLAlchemyAdapterTestCase):

    def setUp(self):
        """
        Make the adapter writable before every test.
        """
        super(ReadOnlySQLStorageAdapterTestCase, self).setUp()
        self.adapter.read_only = False

    def test_update_does_not_add_new_statement(self):
        self.adapter.read_only = True

        statement = Statement("New statement")
        self.adapter.update(statement)

        results = self.adapter.filter(text="New statement")
        self.assertEqual(len(results), 0)

    def test_update_does_not_modify_existing_statement(self):
        statement = Statement("New statement")
        self.adapter.update(statement)

        self.adapter.read_only = True

        statement.in_response_to = "New response"
        self.adapter.update(statement)

        results = self.adapter.filter(text="New statement")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].text, statement.text)
        self.assertEqual(results[0].in_response_to, None)
