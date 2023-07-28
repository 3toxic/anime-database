from config import logpath

def logRead(site):
    with open(logpath, "r") as f:
        lines = f.readlines()
        page = [x for x in lines if site in x]
        return int("".join([i for i in page[0] if i.isdigit()]))

class ScrapeLog():
    def __init__(self):
        self.mal = logRead("mal")
        self.anidb = logRead("anidb")
        self.anilist = logRead("anilist")

    def getMal(self):
        return self.mal

    def getAnidb(self):
        return self.anidb
    
    def getAnilist(self):
        return self.anilist
    
    def progUpdate(self, site, n):
        with open(logpath, 'r') as g:
            lines = g.readlines()

        with open(logpath, 'w') as f:
            error = lines.index([x for x in lines if "Error" in x][0])
            for i, line in enumerate(lines):
                if i<error-1 and site in line:
                    f.write(f"{site.lower()} = {n}\n")
                elif i==error-1:
                    f.write('\n')
                else:
                    f.write(line)

    def writeError(self, str):
        with open(logpath, "a") as f:
            f.write(str + '\n')
    
    def clearError(self):
        with open(logpath, 'r') as g:
            lines = g.readlines()

        with open(logpath, 'w') as f:
            error = lines.index([x for x in lines if "Error" in x][0])
            for i, line in enumerate(lines):
                if i<=error:
                    f.write(line)
                else:
                    break

class MyIter():

    def __init__(self, item):
        self.a = 0
        self.iterable = item
    def __iter__(self):
        return self
    
    def __next__(self):
        if self.a<len(self.iterable):
            x = self.a
            self.a += 1
            return self.iterable[x]
        else:
            raise StopIteration
        

if __name__=="__main__":
    log = ScrapeLog()
    print(log.anidb, log.anilist, log.mal)
    log.writeError("ur mom gay")
    # log.clearError()