from openpyxl import Workbook
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from tools.logger import Logger
from contextlib import contextmanager


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

    def __init__(self, head_line, save_path):
        self.lg = Logger()
        cls = self
        self.head_line = head_line
        self.save_path = save_path
        self.write_headline()

    def write_headline(self):
        with open(self.save_path, 'a+') as f:
            line = [str(i) for i in self.head_line]
            f.write(','.join(line) + '\n')

    @contextmanager
    def write_body(self, file, *args):
        for i in range(len(args[1])):
            line = []
            for j in range(len(args)):
                line.append(args[j][i])
            line = ','.join([str(i) for i in line]) + '\n'
            file.write(line)
            file.flush()
        yield file
        self.lg.info('Write Done!')
