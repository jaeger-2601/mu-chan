import psycopg2.pool
from collections import namedtuple

class Database:

    def __init__(self, app):

        try:
            print('Connecting to PostgreSQL database')

            self.connection_pool = psycopg2.pool.ThreadedConnectionPool(
                minconn=1,
                maxconn=10,
                database=app.config['DB_NAME'], 
                user=app.config['DB_USER'], 
                password=app.config['DB_PASSWORD'], 
                host=app.config['DB_HOST'], 
                port=app.config['DB_PORT']
            )

          
        except Exception as error:
            raise ConnectionError('Could not connect to PostgreSQL database') from error
            
        else:
            print('Connection established with database.')

    def query(self, query, vars_=(), fetch=False, commit=True):

        try:
            connection = self.connection_pool.getconn()

            with connection.cursor() as cursor:           
                cursor.execute(query, vars_)
                
                if commit:
                    connection.commit()

                result = [] if not fetch else cursor.fetchall()

            self.connection_pool.putconn(connection)
            return result

        except Exception as error:
            print('Error execting query "{}", error: {}'.format(query, error))
            return None


    def close_db(self, *args, **kwargs):
        print('Closing connection to database. Goodbye')
        self.connection_pool.closeall()
    
    def __del__(self):
        self.close_db()

class Model:

    schema = ''

    def __init_subclass__(cls, **kwargs):
        pass


    @classmethod
    def _set_db(cls, db):
        cls.db = db


    @classmethod
    def create(cls) -> None:
        print(f'Creating table for {cls.__name__}')
        cls.db.query(cls.schema)

    @classmethod
    def add(cls, **attributes):
        
        query_string = f''' 
        INSERT INTO {cls.__name__.upper()}({','.join([attr.upper() for attr in attributes.keys()])})
        VALUES({','.join(['%s' for _ in attributes.keys()])});'''
        
        cls.db.query(
            query_string, 
            vars_= (*attributes.values(), ), 
            commit=True
        )
        
    @classmethod
    def update(cls, condition, condition_vars, **attributes):

        query_string = f'''
        UPDATE {cls.__name__.upper()}
        SET {','.join([attr.upper() + ' = %s' for attr in attributes.keys()])}
        WHERE {condition};'''

        cls.db.query(
            query_string, 
            vars_= (*attributes.values(), *condition_vars), 
            commit=True
        )

    @classmethod
    def filter_by(cls, condition, condition_vars):
        query_string = f'''
        SELECT * FROM {cls.__name__.upper()}
        WHERE {condition};
        '''

        return cls.db.query(
            query_string, 
            vars_= condition_vars, 
            fetch=True
        )
    @classmethod   
    def get(cls, condition, condition_vars, attributes):

        query_string = f'''
        SELECT {','.join(attributes)} FROM {cls.__name__.upper()}
        WHERE {condition};
        '''

        return cls.db.query(
            query_string, 
            vars_= condition_vars, 
            fetch=True
        )


class Users(Model):
    
    schema = '''
        
        DROP TYPE IF EXISTS USER_TYPE CASCADE;
        CREATE TYPE USER_TYPE AS ENUM (
            'MODERATOR', 'USER'
        ); 
        
        CREATE TABLE IF NOT EXISTS USERS (
            UID SERIAL PRIMARY KEY,
            UNAME VARCHAR(60) UNIQUE NOT NULL,
            EMAIL VARCHAR(100) UNIQUE NOT NULL,
            PWDHASH CHAR(60) NOT NULL,
            DOJ DATE,
            DOB DATE NOT NULL,
            PIC VARCHAR(200),
            UTYPE USER_TYPE DEFAULT 'USER'
        );
    '''

    User = namedtuple('User', ('uid', 'user_name', 'email', 'pwdhash', 'doj', 'dob', 'pic', 'user_type'))

    @classmethod
    def is_unique(cls, attribute, value) -> bool:

        return len(
            cls.db.query(
                f'''
                SELECT * FROM {cls.__name__.upper()}
                WHERE {attribute.upper()} = %s;
                ''', 
                vars_=(value,),
                fetch=True
            )
        ) == 0

    @classmethod
    def is_registered(cls, **attributes) -> bool:

        return len(
            cls.db.query(
                f'''
                SELECT UID FROM {cls.__name__.upper()}
                WHERE {' AND '.join([attr.upper() + ' = %s' for attr in attributes.keys()])};
                ''',
                vars_=(*attributes.values(), ),
                fetch=True,
            )

        ) == 1

    @classmethod
    def is_confirmed(cls, **attributes) -> bool:

        return len(
            cls.db.query(
                f'''
                SELECT UID FROM {cls.__name__.upper()}
                WHERE {' AND '.join([attr.upper() + ' = %s' for attr in attributes.keys()])}
                AND DOJ IS NOT NULL;
                ''',
            vars_=(*attributes.values(), ),
            fetch=True,
            )
        ) == 1
        
    @classmethod
    def get_user_info(cls, **attributes):
        results = cls.db.query(
                f'''
                SELECT * FROM {cls.__name__.upper()}
                WHERE {' AND '.join([attr.upper() + ' = %s' for attr in attributes.keys()])}
                ''',
            vars_=(*attributes.values(), ),
            fetch=True,
            )
        parsed_output = []

        for row in results:
            parsed_output.append(cls.User(*row))

        return parsed_output
        
class Boards(Model):     
    
    schema = '''
        CREATE TABLE IF NOT EXISTS BOARDS (
            BID SERIAL PRIMARY KEY,
            BNAME VARCHAR(60) UNIQUE NOT NULL,
            URL VARCHAR(200) UNIQUE NOT NULL,
            TITLE VARCHAR(60) NOT NULL,
            DESCRIPTION VARCHAR(200) NOT NULL,
            PIC VARCHAR(200)
        );
    '''  
    
class Threads(Model):

    Thread = namedtuple('Thread', ('tid', 'url', 'title', 'description', 'pic', 'upvotes', 'bid', 'uid', 'post_count'))

    schema = '''
        CREATE TABLE IF NOT EXISTS THREADS (
            TID SERIAL PRIMARY KEY,
            URL VARCHAR(200) UNIQUE NOT NULL,
            TITLE VARCHAR(200) NOT NULL,
            DESCRIPTION VARCHAR(40000),
            PIC VARCHAR(200),
            UPVOTES INT NOT NULL DEFAULT 0,
            BID INT REFERENCES BOARDS(BID),
            UID INT REFERENCES USERS(UID) ON DELETE SET NULL
        );

        CREATE OR REPLACE FUNCTION get_post_count(p_tid integer) RETURNS integer AS $$
        BEGIN
                RETURN (SELECT COUNT(TID) FROM POSTS WHERE POSTS.TID = p_tid);
        END;
        $$ LANGUAGE plpgsql;
    '''   

    @classmethod
    def filter_by_board_url(cls, board_url, sort_by, offset, rows_no):
        
        if sort_by == 'replies':

            results = cls.db.query(
                f'''SELECT THREADS.*, get_post_count(THREADS.TID) as post_count
                    FROM BOARDS, THREADS
                    WHERE BOARDS.BID = THREADS.BID AND BOARDS.URL = %s
                    ORDER BY get_post_count(THREADS.TID) DESC
                    OFFSET {offset} ROWS
                    FETCH NEXT {rows_no} ROWS ONLY;
                ''',
                vars_=(board_url,),
                fetch=True
            )

        elif sort_by == 'upvotes':

            results = cls.db.query(
                f'''SELECT THREADS.*, get_post_count(THREADS.TID) as post_count
                    FROM BOARDS, THREADS
                    WHERE BOARDS.BID = THREADS.BID AND BOARDS.URL = %s
                    ORDER BY UPVOTES DESC
                    OFFSET {offset} ROWS
                    FETCH NEXT {rows_no} ROWS ONLY;
                ''',
                vars_=(board_url,),
                fetch=True
            )

        else:
            raise Exception('sort_by method not found')
        
        return [cls.Thread(*row) for row in results]
        
class Posts(Model):

    schema = '''
        CREATE TABLE IF NOT EXISTS POSTS (
            PID SERIAL PRIMARY KEY,
            URL VARCHAR(200) UNIQUE NOT NULL,
            TEXT VARCHAR(40000),
            PIC VARCHAR(200),
            UPVOTES INT NOT NULL DEFAULT 0,
            TID INT REFERENCES THREADS(TID) ON DELETE CASCADE,
            UID INT REFERENCES USERS(UID) ON DELETE SET NULL
        );
    '''

    Post = namedtuple('Post', ('pid', 'url', 'text', 'pic', 'upvotes', 'tid', 'uid', 'user_name', 'user_pic_url'))

    @classmethod
    def filter_by_thread_url(cls, thread_url):
        

        results = cls.db.query(
            f'''SELECT POSTS.*, USERS.UNAME, USERS.PIC
                FROM THREADS, POSTS, USERS
                WHERE THREADS.TID = POSTS.TID AND THREADS.URL = %s
                      AND POSTS.UID = USERS.UID
                ORDER BY POSTS.UPVOTES DESC;
            ''',
            vars_=(thread_url,),
            fetch=True
        )

        
        return [cls.Post(*row) for row in results]

def init_app(app):

    Model._set_db(Database(app))

    @app.cli.command('create_tables')
    def create_tables():
        for model in Model.__subclasses__():
            model.create()

    @app.cli.command('create_boards')
    def create_boards():

        for board in app.config['BOARDS']:
            print(f'Creating {board} board')
            Boards.add(
                BNAME = board,
                URL = board.lower().replace(' ', '_'),
                TITLE = board,
                DESCRIPTION = f'Discussions related to {board}',
                PIC = f''
            )


