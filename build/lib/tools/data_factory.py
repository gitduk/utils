from openpyxl import Workbook
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from tools.logger import Logger
from contextlib import contextmanager

lg = Logger()


class Sql(object):

    def __init__(self, user, password, port, dbname, char, base):
        self.engine = create_engine(
            'mysql://{}:{}@localhost:{}/{}?charset={}'.format(user, password, port, dbname, char),
            echo=False)
        self.__Base = base
        self.__Base.metadata.create_all(self.engine)
        self.__Session = sessionmaker(bind=self.engine)
        self.__session = self.__Session()

    def write(self, msg):
        self.__session.add(msg)
        self.__session.commit()

    @property
    def session(self):
        return self.__session


class Excel(object):
    def __init__(self, path):
        self.wb = Workbook()
        self.sheet = self.wb.active
        self.path = path + '.xlsx'

    def write_headline(self, head_tag_list, head_title_list):
        head_tag_list = list(head_tag_list)
        for i, h in enumerate(head_title_list):
            self.sheet[head_tag_list[i] + '1'] = h
        self.wb.save(self.path)

    def save(self):
        self.wb.save(self.path)


class Csv(object):

    def __init__(self, save_path):
        self.save_path = save_path

    def write_line(self, line):
        with open(self.save_path, 'a+') as f:
            line = [str(i) for i in line]
            f.write(','.join(line) + '\n')

    @lg.log()
    def write_body(self, *args):
        with open(self.save_path, 'a+') as f:
            for i in zip(*args):
                line = ','.join(i) + '\n'
                f.write(line)
                f.flush()
            lg.info('Write Done!')

    @lg.log()
    def write_lines(self, data):
        with open(self.save_path, 'a+') as f:
            for i in data:
                f.write(i)
                f.flush()
            lg.info('Write Done!')
