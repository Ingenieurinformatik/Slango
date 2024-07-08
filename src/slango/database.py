from neo4j import GraphDatabase


class NeoDriver:
    def __init__(self, uri, user, password, db):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.db = db

    def close(self):
        self.driver.close()

    def run_query(self, query):
        with self.driver.session(database=self.db) as session:
            df = session.execute_write(self._run_and_return, query)
            return df

    def run_with_params(self, query, params=None):
        with self.driver.session(database=self.db) as session:
            df = session.execute_write(self._run_and_return, query, params)
            # result = session.run(query, params)
            return df

    @staticmethod
    def _run_and_return(tx, query, params=None):
        result = tx.run(query, params)
        return result.to_df()


# test the driver

__driver = None


def get_database(db):
    global __driver
    if __driver is None:
        __driver = NeoDriver("bolt://localhost:8687", "neo4j", "password", db=db)

    return __driver
