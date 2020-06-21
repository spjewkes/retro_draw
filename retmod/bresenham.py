class BresenhamLine:
    def __init__(self, start, end):
        self.x = start[0]
        self.y = start[1]
        self.w = end[0] - self.x
        self.h = end[1] - self.y
        
        self.dx1, self.dy1, self.dx2, self.dy2 = 0, 0, 0, 0
        
        if self.w < 0:
            self.dx1 = -1
            self.dx2 = -1
        elif self.w > 0:
            self.dx1 = 1
            self.dx2 = 1
        
        if self.h < 0:
            self.dy1 = -1
        elif self.h > 0:
            self.dy1 = 1

        self.longest = abs(self.w)
        self.shortest = abs(self.h)  
        
        if self.shortest >= self.longest:
            self.longest, self.shortest = self.shortest, self.longest
            if self.h < 0:
                self.dy2 = -1
            elif self.h > 0:
                self.dy2 = 1
            self.dx2 = 0
                
        self.numerator = self.longest / 2
        self.count = 0
        
    def __iter__(self):
        return self
    
    def __next__(self):
        if self.count < self.longest:
            retval = (self.x, self.y)
            
            self.numerator += self.shortest
            
            if self.numerator >= self.longest:
                self.numerator -= self.longest
                self.x += self.dx1
                self.y += self.dy1
            else:
                self.x += self.dx2
                self.y += self.dy2
                
            self.count += 1
            return retval

        raise StopIteration
