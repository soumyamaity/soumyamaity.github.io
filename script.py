import os
import yaml
from datetime import datetime




def update_weight(filename):
    with open(filename, 'r') as file:
        lines = file.readlines()
    print("file opened")   
    front_matter = []
    content = []
    in_front_matter = False
    for line in lines:
        if line.strip() == '---':
            in_front_matter = not in_front_matter
        elif in_front_matter:
            front_matter.append(line)
        else:
            content.append(line)
    
    if (not front_matter):
        print("no Frontmatter found")
        return


    try:
        # Parse the front matter as YAML
        front_matter_dict = yaml.safe_load('\n'.join(front_matter))

        #calculate weight       
        post_date = front_matter_dict['date']
        weight = str(post_date.year - 2000) + ('0'+ str(post_date.month) if (post_date.month<10) else str(post_date.month)) + ('0'+ str(post_date.day) if (post_date.day<10) else str(post_date.day)) 
        weight = 1000000 - int(weight)
        print("Weight to be updated:"  + str(weight))
        # Update the weight value here
        front_matter_dict['menu']['sidebar']['weight'] = weight

        updated_front_matter = yaml.safe_dump(front_matter_dict)
        with open(filename, 'w') as file:
            file.write('---\n')
            file.write(updated_front_matter)
            file.write('---\n')
            file.writelines(content)

    except Exception as Error: 
        print(Error)


    # Write the updated front matter and content back to the file
    
   




def main():
    folder_path = 'content/posts/InfoSec/'

    for root, dirs, files in os.walk(folder_path):
        for file in files:
            if file.endswith('.md'):
                file_path = os.path.join(root, file)
                print("Processing for  " + file_path + ":")
                update_weight(file_path)




if __name__ == '__main__':
    main()

