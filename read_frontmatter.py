import yaml

def read_and_update_md_front_matter(filename, updates):
    with open(filename, 'r') as file:
        lines = file.readlines()
        
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
    
    # Parse the front matter as YAML
    front_matter_dict = yaml.safe_load('\n'.join(front_matter))
    
    # Update the front matter
    front_matter_dict['menu']['sidebar']['weight'] = 10000
    
    # Convert the updated front matter back to YAML
    updated_front_matter = yaml.safe_dump(front_matter_dict)
    
    # Write the updated front matter and content back to the file
    with open(filename, 'w') as file:
        file.write('---\n')
        file.write(updated_front_matter)
        file.write('---\n')
        file.writelines(content)

# Test the function
filename = "content/posts/InfoSec/Fuzz-testing/index.md"  # replace with your filename
updates = {'weight': '100'}  # replace with your updates
read_and_update_md_front_matter(filename, updates)
