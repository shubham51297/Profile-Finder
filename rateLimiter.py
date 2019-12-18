import requests
import json
import csv
import os
import time
import threading
import time
from operator import itemgetter
loginId=list()  #Stores the loginId of all the Developers
errorlist=list() #Stores the username of developers when API fails
allUserInfo=list() #Stores the information of all developers

# Function to check if the file exists in current Directory
def exists(path):
    try:
        st=os.stat(path)
    except os.error:
        return False
    return True

# Function to get the list of file records
def getFileData(filename):
    if exists('./'+str(filename)):
        with open(filename,'r') as fileDescriptor:
            csvReader=csv.reader(fileDescriptor)
            next(csvReader)  # Skips the fields header
            dataList=[]
            for line in csvReader:  # Reading one record from file at a time
                singleDeveloper=[]
                singleDeveloper.append(line[0])
                singleDeveloper.append(line[1])
                try:
                    singleDeveloper.append(line[2])
                except:
                    singleDeveloper.append("")
                dataList.append(singleDeveloper) # Adding the the single record to list of record
            return dataList
    else:
        return False

# Function to get the username of first 200 developer for given name and locaion
def getUsername(user):
    resultList=list()
    resultList2=list()
    name=user[0]+" "+user[1]
    location=user[2]
    # REST API request  url for Developer with given name and location
    url="https://api.github.com/search/users?q=\""+name+"\"in:fullname+location:\""+location+"\"&per_page=100&page=1"
    res=requests.get(url,auth=('shubham51297','9f9894c24f91f96376099437e75798eced357fd2'))#Request for Developer
    if(res.json()['total_count']==0) : # If number of developer are Zero
        return
    resultList2=res.json()['items']
    if 'next' in res.links.keys(): # Paging through the search request
        res=requests.get(res.links['next']['url'],auth=('shubham51297','9f9894c24f91f96376099437e75798eced357fd2'))
        resultList=res.json()['items']
    mergelist=resultList+resultList2 # Adding the result of both search page
    for items in mergelist: # Getting the Username of All Developers
        loginId.append(items['login'])

# Function to get the repository in with developer is contributing and its commit count 
def getRepos(username,id):
    try:
        reposList=list()
        url = 'https://api.github.com/graphql'# GraphQL API request url
        # GraphQL query json object
        json = { 'query' : '{user(login: "'+str(username)+'") {repositories(first:100) {pageInfo {startCursor hasNextPage endCursor} nodes {name ref(qualifiedName: "master"){target{ ... on Commit{ history(author: { id: "'+str(id)+'" }){ totalCount}    					}						}				}      }    }  }}' }
        api_token = "9f9894c24f91f96376099437e75798eced357fd2" # Authenticaton Token
        headers = {'Authorization': 'token %s' % api_token} 
        r = requests.post(url=url, json=json,headers=headers) # Request the json object for repository and their count
        allRepos=r.json()['data']['user']['repositories']['nodes']  # Get  list repository and their count
        nextPage=r.json()['data']['user']['repositories']['pageInfo']['hasNextPage'] # Next page cursor of search result
        for oneRepos in allRepos: # Getting Individual repository commit count
            if oneRepos['ref']==None: # If No path is provided
                continue
            count=oneRepos['ref']['target']['history']['totalCount']
            name=oneRepos['name']
            if count>0: # If one or more commit is there
                reposList.append([name,count])
        #Paging through the search result for next page
        while nextPage:
            endCursor=r.json()['data']['user']['repositories']['pageInfo']['endCursor']
            json={ 'query' : '{user(login: "'+str(username)+'") {repositories(first:100,after:"'+str(endCursor)+'") {pageInfo {startCursor hasNextPage endCursor} nodes {name ref(qualifiedName: "master"){target{ ... on Commit{ history(author: { id: "'+str(id)+'" }){ totalCount}    					}						}				}      }    }  }}' }
            r = requests.post(url=url, json=json,headers=headers)
            allRepos=r.json()['data']['user']['repositories']['nodes']
            nextPage=r.json()['data']['user']['repositories']['pageInfo']['hasNextPage']
            for oneRepos in allRepos:
                if oneRepos['ref']==None:
                    continue
                count=oneRepos['ref']['target']['history']['totalCount']
                name=oneRepos['name']
                if count>0:
                    reposList.append([name,count])
        return reposList
    except:
        errorlist.append(username) # When the API fail for that particular username
        return ["null"]
    

# Function to get the public information of singal developer
def getUserInfo ( user ):
    
    userUrl = "https://api.github.com/users/"+user  # REST API call url for developer information
    userRequest = requests.get(url = userUrl,auth=('shubham51297', '9f9894c24f91f96376099437e75798eced357fd2'))
    userData =  userRequest.json() 
    singleUser = dict()

    if userData['name']== None: # If name is not provided
            singleUser['name'] = "~"
    else :
        singleUser['name'] = userData['name'].upper()
    singleUser['login'] = userData['login']
    singleUser['company'] = userData['company']
    singleUser['email'] = userData['email']
    singleUser['location'] = userData['location']
    singleUser['bio'] = userData['bio']
    singleUser['hireable'] = userData['hireable']
    singleUser['node_id'] = userData['node_id']
    allUserInfo.append(singleUser) # Adding the information to list of developers

# Function To write the results to csv file
def writeUserData( userDataList):
    csvFileColumns = ['name', 'login', 'company', 'email','location', 'bio', 'hireable','node_id','repos']
    csvFile = "output.csv"

    with open(csvFile,'a',encoding="UTF-8",newline='') as fileDescriptor:
        writer = csv.DictWriter(fileDescriptor, fieldnames=csvFileColumns)
        writer.writerow({'name':'name','login':'login','company':'company','email':'email','location':'location','bio':'bio','hireable':'hireable','node_id':'node_id','repos':'[repository,count]'})
        for data in userDataList:
            writer.writerow(data)
    
        

if __name__ == '__main__':
    
    startTime=time.time()  # stores the starting time of program
    
    inputFileName=input('Enter the input filename \n')

    userData=getFileData(inputFileName)    # gets the list of first name,last name and location from the input file
    if userData == False :
        print('No such file in the current Directory')
        exit(0)
    
    # To get the usernames of developers for a given first name,last name and location
    try:
        threads = [threading.Thread(target=getUsername, args=(user,)) for user in userData]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
    except:
        print()

    
    # To get the public information of user
    try:
        threads = [threading.Thread(target=getUserInfo, args=(oneId,)) for oneId in loginId]
        for thread in threads:
            time.sleep(.1)
            thread.start()
        for thread in threads:
            thread.join()
    except:
        print()
    
    print('Number of Developer : '+str(len(allUserInfo)))
    count=0
    # To get the public repos and count for the user
    for oneUser in allUserInfo:
        count+=1
        print(oneUser['login']+' '+str(count))
        reposList=getRepos(oneUser['login'],oneUser['node_id'])
        oneUser['repos']=reposList

    print('Number of api falut : '+str(len(errorlist)))
    print((errorlist))        
    allUserInfo.sort(key=itemgetter('name'))  # Sorting the records in alphabetical order
    
    writeUserData(allUserInfo)
    
    print('Total time of execution : '+str(time.time()-startTime))
