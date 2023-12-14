def integratel(f,a,b,n):
    a1 = float(a)
    b1 = float(b)
    y = 0
    for i in range(0,n):
        y = y + f(a1 + (b1-a1)*i/n)
    return y*(b1-a1)/n

def acctfn(k,a,b,c,m):
    return lambda x : max(x/(k - a*x - b*x**2 - c*x**3), 1/m)

def dectfn(k,a,b,c,m):
    return lambda x : max(x/(k + a*x + b*x**2 + c*x**3), 1/m)

def accdfn(k,a,b,c,m):
    return lambda x : max((x**2)/(k - a*x - b*x**2 - c*x**3), x/m)

def decdfn(k,a,b,c,m):
    return lambda x : max((x**2)/(k + a*x + b*x**2 + c*x**3), x/m)

def acctime(k,a,b,c,m,x1,x2,n):
    if x1 <= x2:
        return integratel(acctfn(k,a,b,c,m),x1,x2,n)
    else:
        return integratel(acctfn(k,a,b,c,m),x2,x1,n)

def dectime(k,a,b,c,m,x1,x2,n):
    if x1 <= x2:
        return integratel(dectfn(k,a,b,c,m),x1,x2,n)
    else:
        return integratel(dectfn(k,a,b,c,m),x2,x1,n)
    
def accdist(k,a,b,c,m,x1,x2,n):
    if x1 <= x2:
        return integratel(accdfn(k,a,b,c,m),x1,x2,n)
    else:
        return integratel(accdfn(k,a,b,c,m),x2,x1,n)
    
def decdist(k,a,b,c,m,x1,x2,n):
    if x1 <= x2:
        return integratel(decdfn(k,a,b,c,m),x1,x2,n)
    else:
        return integratel(decdfn(k,a,b,c,m),x2,x1,n)
    
def accpen(k,a,b,c,m,x1,x2,n):
    return acctime(k,a,b,c,m,x1,x2,n) - accdist(k,a,b,c,m,x1,x2,n)/max(x1, x2)

def decpen(k,a,b,c,m,x1,x2,n):
    return dectime(k,a,b,c,m,x1,x2,n) - decdist(k,a,b,c,m,x1,x2,n)/max(x1, x2)

def slowpen(k,a,b,c,m,x1,x2,n):
    return accpen(k,a,b,c,m,x1,x2,n) + decpen(k,a,b,c,m,x1,x2,n)

def speedzone(k,a,b,c,m,u,v,n):
    if len(u) - len(v) != 1:
        return "error, v must have length 1 less than u."
    if min(v) <= 0:
        return "error, all speed zones must be positive."
    r = []
    r.append(0.5*slowpen(k,a,b,c,m,0,v[0],n))
    for i in range(len(v)-1):
        r.append(1000*(u[i+1]-u[i])/v[i])
        r.append(0.5*slowpen(k,a,b,c,m,v[i],v[i+1],n))
    r.append(1000*(u[len(v)]-u[len(v)-1])/v[len(v)-1])
    r.append(0.5*slowpen(k,a,b,c,m,0,v[len(v)-1],n))
    return r

def speedzonek(k,a,b,c,m,u,v,n):
    w = []
    for i in range(len(v)):
        w.append(v[i]/3.6)
    return speedzone(k,a,b,c,m,u,w,n)
            
            

print ("This is a train performance calculator.")
print ("Please input the train's performance specs:")
print ("k is power/weight ratio in kW/t. For N700 Shinkansen, use 26.74. For a generic train, use 20.")
print ("m is initial acceleration in m/s^2. For N700, use 0.9; for generic, use 0.5.")
print ("a, b, c are the constant, linear, quadratic terms in track resistance.")
print ("For X2000, use a = 0.0059, b = 0.000118, c = 0.000022.")
print ("For latest-model HSR, use c = 0.000012.")
print ("Use accpen and decpen for acceleration/deceleration penalties from speed x1 to x2 m/s, where x2 > x1. slowpen = accpen + decpen.")
print ("Input an arbitrary large integer for n. Try n = 500.")
print ("You can also use speedzone and speedzonek to compute trip times from speed zones.")
print ("u is the array of km-points, v is a paired list of speed zones length 1 less than u.")
print ("For v in m/s, use speedzone. For v in km/h, use speedzonek.")
print ("speedzone and speedzonek give arrays; use sum for overall trip time.")
