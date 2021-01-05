
import csv


def write_csv_file(path,head,row,mode='r'):  
    WriterLog=True
    if WriterLog==False:
        return
    try:  
        with open(path,mode,newline='') as csv_file:  
            writer = csv.writer(csv_file, dialect='excel')  
  
            if head is not None: 
                csv_file.truncate()
                writer.writerow(head)  
  
            if row is not None:
                writer.writerow(row)  
  
            print("Write a CSV file to path %s Successful." % path)  
    except Exception as e:  
        print("Write an CSV file to path: %s, Case: %s" % (path, e)) 