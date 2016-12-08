# Ansible_Aws_SipXcom

**Deploy sipXcom EC2 devops style**

**How to deploy sipXcom in AWS DevOps style**

Since some of our users and our QA department is using AWS to run and test sipXcom deployments we decided to write a series of blogs on how to automatically deploy and configure sipXcom on Amazon Web Services.

Our sipXcom/Uniteme hardware agnostic software design is a perfect match for DevOps style of creating/configuring and terminating machines on demand.

To do so we will use the build-in modules of Ansible that can access AWS API’s to create, configure and terminate EC2 instances.

We will use [Ansible](http://docs.ansible.com/ansible/guide_aws.html ) website’s well written documentation and examples


We’ve also utilized knowledge shared by [linuxacademy](https://linuxacademy.com/) on various channels.

#### **PART 1** _Provisioning a minimal CentOS machine with Ansible-AWS,  used to create our own sipXcom based AMI_

In the first blog entry we will use AWS API’s and Ansible EC2 module to create a base CentOS 6.7 image. Now we will further prepare for the installation of sipXcom. 

This will be an intermediary level where basic knowledge of AWS and Ansible are prerequisites.

First let’s create a folder where we will add our project files:
```
mkdir   Ansible_AWS_SipXcom
cd      Ansible_AWS_SipXcom
```

**Step 1. Create an AWS IAM role to be used by Ansible.**

![IAM](./images/1.png)

Under the upper right screen of your AWS console, under your profile click on the Security Credentials.
From the left side tab select Users menu and create a new user. In our case this is called “devops”. You would want to assign permissions for this user, in our Proof of Concept we will give him unlimited powers.

Next, create an access key. This is very important and you need to make sure you save these credentials in a safe place.

![Access Key](./images/2.png)



**Step 2. Preparing Ansible.**
Next we will copy those credential into configuration files that we will use inside the Ansible playbook. First let’s create a folder called “files”.
```
mkdir files
cd files
pwd
~/Ansible_AWS_SipXcom/files
ll
-rw-r--r--. 1 mcostache mcostache 101 Aug 30 20:45 awscreds.yml
-rw-r--r--. 1 mcostache mcostache 198 Aug 30 20:56 info.yml
```

File awscreds.yml should contain your own credentials and the region you would like to use when launching your server.

 ```
cat awscreds.yml
aws_key: Ds5dm--**********
aws_id: AKIA--********* 
aws_region: eu-west-1
 ```

File info.yml will contain base ami we want to use and other AWS related information like machine size and security-group used:

```
cat info.yml
standard_ami: ami-edb9069e
sipxcom_ami: ami-e3f1d694
tiny_instance: t1.micro
free_instance: t2.micro
large_instance: m4.large
ssh_keyname: devops-key
inst_id:
template_id:
secgroup_id: sg-9a-**********
```

Defining the above configuration files will help us increase the level of abstraction used in the main playbook.

```
cd ..
ll
-rw-r--r--. 1 mcostache mcostache  726 Aug 30 21:05 centos_provision.yml
drwxr-xr-x. 2 mcostache mcostache 4096 Aug 31 11:23 files
```


Let’s take a look at the main playbook by using cat command:

```
cat centos_provision.yml
---
- hosts: localhost                #since we will use AWS API’ we will run not need SSH (for now...)
  connection: local
  remote_user: devops       #AWS IAM user defined
  gather_facts: no
  vars_files:
  - files/awscreds.yml       #credential files
  - files/info.yml                 #machine sizing and used AMI
  tasks:
  - name: Basic provisioning of EC2 instance
    ec2:
      aws_access_key: "{{ aws_id }}"   
      aws_secret_key: "{{ aws_key }}"
      region: "{{ aws_region }}"
      image: "{{ standard_ami }}"
      instance_type: "{{ large_instance }}"
      key_name: "{{ ssh_keyname }}"
      count: 1
      state: present
      group_id: "{{ secgroup_id }}"
      wait: no
      vpc_subnet_id: subnet-********
      assign_public_ip: yes
      instance_tags:
        Name: centOS_template
    register: ec2info
  - name: Print the results
    debug: var=ec2info
```

aws_access_key: "{{ aws_id }}"  -- will use aws_id: AKIA--********** defined in awscreds.yml and so on, you get the point...

**Step 3. Run Ansible playbook and configure root access for CentOS image**

Notes:
EC2 Ansible modules requires python >= 2.6 and boto. Make sure you have them installed. On my Fedora machine I’ve used pip install boto command 
I’ve used instructions from here to enable root access for AMI: http://gurjeet-tech.blogspot.ro/2012/02/allowing-root-access-in-amis.html

```
 pwd
~/Ansible_AWS_SipXcom

ansible-playbook centos_provision.yml
 [WARNING]: provided hosts list is empty, only localhost is available


PLAY [localhost] ***************************************************************

TASK [Basic provisioning of EC2 instance] **************************************
changed: [localhost]

…………………………………………………………………………………………

PLAY RECAP *********************************************************************
localhost                  : ok=2    changed=1    unreachable=0    failed=0 
```

Now let’s get on the AWS console interface under Services-EC2 you should see something like this picture:

![EC2](./images/3.png)

We will wait for the job to be finished then we will grab the public IP address assigned to this instance to allow root login

```
chmod 600 ~/.ssh/devops-key.pem
[mcostache@localhost Ansible_AWS_SipXcom]$ ssh -i ~/.ssh/devops-key.pem centos@52.209.207.51
Last login: Wed Aug 31 08:51:46 2016 from 5.2.152.210
```

Execute these steps directly from centos user cli:

```
$ sudo perl -i -pe 's/disable_root: 1/disable_root: 0/' /etc/cloud/cloud.cfg
$ sudo perl -i -pe 's/#PermitRootLogin .*/PermitRootLogin without-password/' /etc/ssh/sshd_config
$ sudo perl -i -pe 's/.*(ssh-rsa .*)/\1/' /root/.ssh/authorized_keys
$ sudo /etc/init.d/sshd reload # optional command
$ service sshd restart
```

Now you should be able to ssh as root:

```
ssh -i ~/.ssh/devops-key.pem root@52.209.207.51
Last login: Wed Aug 31 08:51:25 2016 from 5.2.152.210
[root@ip-10-0-0-214 ~]#
```


#### **Part 2** - _Creating SipXcom based AMI_

At the end of part 1 we have launched a CentOS prepared EC2 instance that we will use to create our own sipXcom AMI.

**Step 1. Connect to AWS console and gather needed facts for Ansible.**

Under Services - EC2 - Running Instance - menu we will see something like:

![public ip](./images/4.png)

Click on your newly created instance and collect “instance_id” and “public_ip”:

![public ip](./images/5.png)

In our demo: **instance_id = i-8b3a21b5**  and **public_ip = 52.210.220.252**

**Step 2. Configure Ansible to use gathered information from the above step**
```
pwd 
~/Ansible_AWS_SipXcom
```
I like to keep ansible.cfg and inventory.ini in the current path.
```
ls -l
-rw-rw-r-- 1 mihai mihai   55 Aug 23 11:31 ansible.cfg
drwxrwxr-x 2 mihai mihai 4096 Sep  2 13:02 files
-rw-rw-r-- 1 mihai mihai   51 Aug 24 08:54 inventory.ini
-rw-rw-r-- 1 mihai mihai  725 Sep  2 12:49 provision.yml
-rw-rw-r-- 1 mihai mihai  811 Sep  2 12:44 sipxcom_template.yml

cat ansible.cfg
[defaults]
hostfile = inventory.ini
remote_user = root
```

We next need to add an AWS group to our inventory.ini where we will define the public_ip of the newly created CentOS template

```
cat inventory.ini
[aws]
52.210.220.252  ansible_ssh_private_key_file=~/.ssh/devops-key.pem
```

Note the need of private key to connect to AWS instance. We have generated this key in Part 1 under AWS console -- key pair -- devops-key.

Next we will add instance_id in the files/info.yml

```
cd files
cat info.yml
standard_ami: ami-edb9069e
sipxcom_ami: ami-e3f1d694
tiny_instance: t1.micro
free_instance: t2.micro
large_instance: m4.large
ssh_keyname: devops-key
Inst_id: i-8b3a21b5
template_id:
secgroup_id: sg-9a-**********
```

**Step 3. Make a new Ansible playbook to create sipXcom template**

First let’s download sipxcom.repo that we will use to install sipXcom

```
pwd
~/Ansible_AWS_SipXcom/files

wget http://download.sipxcom.org/pub/sipXecs/16.02/sipxecs-16.02.0-centos.repo && mv sipxecs* sipxcom.repo

ls -l
-rw-rw-r-- 1 mihai mihai 101 Aug 30 20:45 awscreds.yml
-rw-rw-r-- 1 mihai mihai 209 Sep  2 13:11 info.yml
-rw-rw-r-- 1 mihai mihai 161 Mar 21 09:24 sipxcom.repo

cd ..
pwd 
~/Ansible_AWS_SipXcom
```

Now we will create an ansible playbook called sipxcom_template.yml with the following content:

```
cat sipxcom_template.yml
---
- hosts: aws         # connect to the aws hosts defined in inventory.ini as root
 remote_user: root
 gather_facts: yes
 connection: ssh
 tasks:
     - name: Copy sipxcom.repo in /etc/yum.repos.d  
       copy: src=files/sipxcom.repo dest=/etc/yum.repos.d/sipxcom.repo
     - name: Installing sipxcom. Go get a coffee. It will take a while 
       yum:  name=sipxcom state=present    # install sipXcom repo after we’ve copy it 

- hosts: localhost      #execute locally AWS api commands section to create sipxcom AMI
  connection: local
  remote_user: devops
  gather_facts: no
  vars_files:
  - files/awscreds.yml
  - files/info.yml
  tasks:
  - name: Basic provisioning of sipXcom AMI
    ec2_ami:                                 # Note we are using ec2_ami module            
      aws_access_key: "{{ aws_id }}"
      aws_secret_key: "{{ aws_key }}"
      region: "{{ aws_region }}"
      instance_id: "{{ inst_id }}"
      wait: no
      name: sipXcom_AMI
      tags:
        Name: sipXcom_16.02
        Service: sipXcom_UC_server
    register: instance
  - name: Print the results
    debug: var=instance
```

**Step 4. Execute ansible-playbook command and visualize the newly created sipXcom template**

```
pwd 
~/Ansible_AWS_SipXcom/

ansible-playbook sipxcom_template.yml

PLAY [aws] *********************************************************************

TASK [setup] *******************************************************************
ok: [52.210.220.252]

TASK [Copy sipxcom.repo in /etc/yum.repos.d] ***********************************
changed: [52.210.220.252]

TASK [Installing sipxcom. Go get a coffee. It will take a while] ********************************************************
changed: [52.210.220.252]

PLAY [localhost] ***************************************************************

TASK [Basic provisioning of sipXcom AMI] ***************************************
changed: [localhost]

TASK [Print the results] *******************************************************
ok: [localhost] => {
    "instance": {
        "architecture": "x86_64",
        "block_device_mapping": {
            "/dev/sda1": {
                "delete_on_termination": false,
                "encrypted": false,
                "size": 8,
                "snapshot_id": "snap-dc188531",
                "volume_type": "standard"
            }
        },
        "changed": true,
        "creationDate": "2016-09-02T10:52:49.000Z",
        "description": null,
        "hypervisor": "xen",
        "image_id": "ami-a8681adb",
        "is_public": false,
        "location": "541233277246/sipXcom_AMI",
        "msg": "AMI creation operation complete",
        "ownerId": "541233277246",
        "root_device_name": "/dev/sda1",
        "root_device_type": "ebs",
        "state": "available",
        "tags": {},
        "virtualization_type": "hvm"
    }
}

PLAY RECAP *********************************************************************
52.210.220.252             : ok=3    changed=2    unreachable=0    failed=0   
localhost                  : ok=2    changed=1    unreachable=0    failed=0   
```


Now let’s see our new shiny sipXcom based AMI.

Connect to AWS console and under AMI sub-menu:

![AMI](./images/6.png)

You should have an entry like this:

![AMI](./images/7.png)


#### **Part 3**-_Create an EC2 instance from sipXcom template and configure newly launched server_

In Part 2 we created a sipXcom based AMI build on the CentOS done in Part 1.

Let’s use that AMI to create our first EC2 sipXcom instance.

**Step 1. Get AMI-id for new sipXcom template**

Connect to your AWS console. Under Images-- AMI’s we have:

![SixpCom Ami](./images/8.png)

Now we should collect ami-b49defc7 and add it to files/info.yml file for  sipxcom_ami: key

```
$ cat files/info.yml
standard_ami: ami-edb9069e
sipxcom_ami: ami-b49defc7
tiny_instance: t1.micro
free_instance: t2.micro
large_instance: m4.large
ssh_keyname: devops-key
inst_id: i-8b3a21b5
template_id:
secgroup_id: sg-*****
sip_domain: mihai.test
sip_realm: mihai.test
net_domain: mihai.test
net_host: uc1
```

Note also sip_domain: mihai.test ;sip_realm: mihai.test;net_domain: mihai.test;net_host: uc1 - we will use these values to configure our sipXcom server with fqdn uc1.mihai.test

**Step 2. Crete playbook that will install EC2 sipXcom server**

```
pwd
~/Ansible_AWS_SipXcom

cat configure_sipxcom.yml
---
- hosts: localhost
  connection: local
  remote_user: devops
  gather_facts: no
  vars_files:
  - files/awscreds.yml
  - files/info.yml
  tasks:
  - name: Basic provisioning of EC2 instance
    ec2:
      aws_access_key: "{{ aws_id }}"
      aws_secret_key: "{{ aws_key }}"
      region: "{{ aws_region }}"
      image: "{{ sipxcom_ami }}"
      instance_type: "{{ free_instance }}"
      key_name: "{{ ssh_keyname }}"
      count: 1
      state: present
      group_id: "{{ secgroup_id }}"
      wait: yes
      vpc_subnet_id: subnet-29a32841
      assign_public_ip: yes
      instance_tags:
        Name: uc1.mihai.test
    register: ec2info

  - name: Print the results
    debug: var=ec2info

#In the first section we will use our newly generated sipXcom template to start an EC2 instance.
#We’ve explain these settings in previous blog posts.

  - name: Add all instance public IPs to host group
    add_host: hostname={{ ec2info.instances[0].public_ip  }}
              groups=ec2hosts
              ansible_ssh_private_key_file=~/.ssh/devops-key.pem

#Above section will help us dynamically populate hostnames under ec2hosts groups since we are not using static IP’s we need to collect them in playbook using ec2info object that provides instance  public IP through  ec2info.instances[0].public_ip attribut.
 
  - name: Wait for SSH to come up
    remote_user: root
    wait_for: host={{ ec2info.instances[0].public_ip  }} port=22 delay=10 timeout=320 state=started
 
#We need to wait for sshd to be up and running on the public IP before configuring server.

- hosts: ec2hosts
  vars_files:
      - files/awscreds.yml
      - files/info.yml
  tasks:
  - name: Configure sipxcom
    remote_user: root
    
    shell: sipxecs-setup --noui --sip_domain "{{ sip_domain }}" --sip_realm "{{ sip_realm }}" --net_domain "{{ net_domain }}" --net_host "{{ net_host }}"    
```

We are connecting to the machine and then we will run sipx-setup in non UI mode by providing needed information which we have already added into the info.yml file.

**Step 3. Connect to your newly created machine, add superadmin password and start services.**

```
pwd
~/Ansible_AWS_SipXcom

ansible-playbook configure_sipxcom.yml

PLAY [localhost] ***************************************************************

TASK [Basic provisioning of EC2 instance] **************************************
changed: [localhost]

TASK [Print the results] *******************************************************
ok: [localhost] => {
    "ec2info": {
        "changed": true,
        "instance_ids": [
            "i-f0896dc1"
        ],
        "instances": [
            {
                "ami_launch_index": "0",
                "architecture": "x86_64",
                "block_device_mapping": {
                    "/dev/sda1": {
                        "delete_on_termination": false,
                        "status": "attached",
                        "volume_id": "vol-c3c62541"
                    }
                },
                "dns_name": "ec2-52-210-185-88.eu-west-1.compute.amazonaws.com",
                "ebs_optimized": false,
                "groups": {
                    "sg-9a9ca7fd": "devops"
                },
                "hypervisor": "xen",
                "id": "i-f0896dc1",
                "image_id": "ami-b49defc7",
                "instance_type": "m4.large",
                "kernel": null,
                "key_name": "devops-key",
                "launch_time": "2016-09-05T11:07:18.000Z",
                "placement": "eu-west-1c",
                "private_dns_name": "ip-10-0-0-180.eu-west-1.compute.internal",
                "private_ip": "10.0.0.180",
                "public_dns_name": "ec2-52-210-185-88.eu-west-1.compute.amazonaws.com",
                "public_ip": "52.210.185.88", ---- NOTE public IP ----
                "ramdisk": null,
                "region": "eu-west-1",
                "root_device_name": "/dev/sda1",
                "root_device_type": "ebs",
                "state": "running",
                "state_code": 16,
                "tags": {
                    "Name": "uc1.mihai.test"
                },
                "tenancy": "default",
                "virtualization_type": "hvm"
            }
        ],
        "tagged_instances": []
    }
}

TASK [Add all instance public IPs to host group] *******************************
changed: [localhost]

TASK [Wait for SSH to come up] *************************************************
ok: [localhost]

PLAY [ec2hosts] ****************************************************************

TASK [setup] *******************************************************************
ok: [52.210.185.88]

TASK [Configure sipxcom] *******************************************************
changed: [52.210.185.88]

PLAY RECAP *********************************************************************
52.210.185.88              : ok=2    changed=1    unreachable=0    failed=0   
localhost                  : ok=4    changed=2    unreachable=0    failed=0   

```


![GUI](./images/9.png)




#### **Part 4**- _Adding AWS Route 53 entries to match a newly created server_

At the end of part 3 we have already created and start running a production ready sipXcom server on AWS EC2 instance.

The only shortcoming was the need to use the server’s IP addresses, but those IPs change as soon as you shut down an instance and who want’s to remember numbers.
 
On this (short) tutorial we will use  Ansible’s route53 module documented here:
http://docs.ansible.com/ansible/route53_module.html


**Step 1. Connect to route 53 service**

Go to  AWS management console → Services → Route 52

![AWS console](./images/10.png)

Get your hosted zone name. In our case this is ezuce.ro

![Hosted zone](./images/11.png)


**Step 2.  Rewrite info.yml to use new hosted zone**
```
cat files/info_hosted.yml

standard_ami: ami-edb9069e
sipxcom_ami: ami-b49defc7
tiny_instance: t1.micro
free_instance: t2.micro
large_instance: m4.large
ssh_keyname: devops-key
inst_id: i-8b3a21b5
template_id:
secgroup_id: sg-9a9ca7fd
sip_domain: mihai.ezuce.ro
sip_realm: mihai.ezuce.ro
net_domain: mihai.ezuce.ro
net_host: uc1
```

Note: ezuce.ro domain.


**Step 3. Create new playbook for configuring EC2 instance**

```
pwd
~/Ansible_AWS_SipXcom/

$ cat configure_sipxcom_named.yml
---
- hosts: localhost
  connection: local
  remote_user: devops
  gather_facts: no
  vars_files:
  - files/awscreds.yml
  - files/info_hosted.yml
  tasks:
  - name: Basic provisioning of EC2 instance
    ec2:
      aws_access_key: "{{ aws_id }}"
      aws_secret_key: "{{ aws_key }}"
      region: "{{ aws_region }}"
      image: "{{ sipxcom_ami }}"
      instance_type: "{{ free_instance }}"
      key_name: "{{ ssh_keyname }}"
      count: 1
      state: present
      group_id: "{{ secgroup_id }}"
      wait: yes
      vpc_subnet_id: subnet-29a32841
      assign_public_ip: yes
      instance_tags:
        Name: uc1.mihai.ezuce.ro
    register: ec2info
  - name: Print the results
    debug: var=ec2info
  - name: Add all instance public IPs to host group
    add_host: hostname={{ ec2info.instances[0].public_ip  }}
              groups=ec2hosts
              ansible_ssh_private_key_file=~/.ssh/devops-key.pem

# We talked about the following section in previous blog articles:
              
  - name: Add Route 53 entries for newly created EC2 Instance
    route53:
      command: create
      zone: ezuce.ro
      record: "{{ net_host }}.{{ net_domain }}"
      type: A
      ttl: 7200
      value: "{{ ec2info.instances[0].public_ip  }}"
      overwrite: yes
```


**For today’s tutorial we will look just at this section:**

 >command: create -self explanatory

 >zone: ezuce.ro   - my hosted zone

 >record: "{{ net_host }}.{{ net_domain }}"  - We want to create an A record that will point to my above (info_hosted.yml) explained FQDN

 >value: "{{ ec2info.instances[0].public_ip  }}" - A record will point to the dynamically changing IP address obtained in ec2info json object

 >overwrite: yes  - Mandatory since our IP will change frequently
 
```
- name: Add TCP SIP  SRV
    route53:
      command: create
      zone: ezuce.ro
      overwrite: yes
      record: "_sip._tcp.{{ net_domain }}."
      type: SRV
      value: "10 10 5060 {{ net_host }}.{{ net_domain }}"
             
  - name: Add UDP SIP  SRV
    route53:
      command: create
      zone: ezuce.ro
           overwrite: yes
      record: "_sip._udp.{{ net_domain }}."
      type: SRV
      value: "10 10 5060 {{ net_host }}.{{ net_domain }}"
```

>With record: "_sip._tcp.{{ net_domain }}." - we are creating DNS SRV’s with TCP and UDP that will have them pointing to "10 10 5060 {{ net_host }}.{{ net_domain }}"

Note: If you want to read more about DNS SRV’s check this link:
http://wiki.sipxcom.org/display/unite/DNS+Concepts

We talked about this section in previous blog articles:
```
  - name: Wait for SSH to come up
    remote_user: root
    wait_for: host={{ ec2info.instances[0].public_ip  }} port=22 delay=10 timeout=320 state=started
```

We talked about this section in previous blog articles:

```
- hosts: ec2hosts
  vars_files:
      - files/awscreds.yml
      - files/info_hosted.yml
  tasks:
  - name: Configure sipxcom
    remote_user: root
    shell: sipxecs-setup --noui --sip_domain "{{ sip_domain }}" --sip_realm "{{ sip_realm }}" --net_domain "{{ net_domain }}" --net_host "{{ net_host }}"
```


**Step 4. Run playbook and connect to Web GUI using FQDN**

```
ansible-playbook configure_sipxcom_named.yml

PLAY [localhost] ***************************************************************

TASK [Basic provisioning of EC2 instance] **************************************
changed: [localhost]

TASK [Print the results] *******************************************************
ok: [localhost] => {
    "ec2info": {
        "changed": true,
        "instance_ids": [
            "i-03ef0b32"
        ],
        "instances": [
            {
                "ami_launch_index": "0",
                "architecture": "x86_64",
                "block_device_mapping": {
                    "/dev/sda1": {
                        "delete_on_termination": false,
                        "status": "attached",
                        "volume_id": "vol-482ac9ca"
                    }
                },
                "dns_name": "ec2-52-210-225-215.eu-west-1.compute.amazonaws.com",
                "ebs_optimized": false,
                "groups": {
                    "sg-9a9ca7fd": "devops"
                },
                "hypervisor": "xen",
                "id": "i-03ef0b32",
                "image_id": "ami-b49defc7",
                "instance_type": "t2.micro",
                "kernel": null,
                "key_name": "devops-key",
                "launch_time": "2016-09-05T13:00:39.000Z",
                "placement": "eu-west-1c",
                "private_dns_name": "ip-10-0-0-48.eu-west-1.compute.internal",
                "private_ip": "10.0.0.48",
                "public_dns_name": "ec2-52-210-225-215.eu-west-1.compute.amazonaws.com",
                "public_ip": "52.210.225.215",
                "ramdisk": null,
                "region": "eu-west-1",
                "root_device_name": "/dev/sda1",
                "root_device_type": "ebs",
                "state": "running",
                "state_code": 16,
                "tags": {
                    "Name": "uc1.mihai.ezuce.ro"
                },
                "tenancy": "default",
                "virtualization_type": "hvm"
            }
        ],
        "tagged_instances": []
    }
}

TASK [Add all instance public IPs to host group] *******************************
changed: [localhost]

TASK [Wait for SSH to come up] *************************************************
ok: [localhost]

TASK [Add Route 53 entries for newly created EC2 Instance] *********************
changed: [localhost]

PLAY [ec2hosts] ****************************************************************

TASK [setup] *******************************************************************
ok: [52.210.225.215]

TASK [Configure sipxcom] *******************************************************
changed: [52.210.225.215]

PLAY RECAP *********************************************************************
52.210.225.215             : ok=2    changed=1    unreachable=0    failed=0   
localhost                  : ok=5    changed=3    unreachable=0    failed=0   
```

Under AWS console -- Route 53 you should see entries like:

![Route 53](./images/12.png)

Now you can access your Web UI by name: 

![FQDN GUI](./images/13.png)


You could also dig for services with:

```
dig -t SRV _sip._tcp.mihai.ezuce.ro
; <<>> DiG 9.10.3-P4-RedHat-9.10.3-9.P4.fc22 <<>> -t SRV _sip._tcp.mihai.ezuce.ro
;; global options: +cmd
;; Got answer:
;; ->>HEADER<<- opcode: QUERY, status: NOERROR, id: 60750
;; flags: qr rd ra; QUERY: 1, ANSWER: 1, AUTHORITY: 0, ADDITIONAL: 1
;; OPT PSEUDOSECTION:
; EDNS: version: 0, flags:; udp: 4096
;; QUESTION SECTION:
;_sip._tcp.mihai.ezuce.ro.    IN    SRV
;; ANSWER SECTION:
_sip._tcp.mihai.ezuce.ro. 3600    IN    SRV    10 10 5060 uc1.mihai.ezuce.ro.
;; Query time: 45 msec
;; SERVER: 192.168.1.1#53(192.168.1.1)
;; WHEN: Wed Sep 07 10:57:36 EEST 2016
;; MSG SIZE  rcvd: 91
```



#### **Part 5**- _Starting services and populating new servers with users, gateways, devices, etc._

In previous parts we’ve demonstrated how to create a sipXcom AMI from a base CentOS template, how to install and configure sipXcom on that template and how to add Route 53 entries that points to that machine.
 
It’s time to bring all together and automate creation of a populate machine.

**Step 1. Add superadmin password from command line interface**

Command that we will use will be an postgres insert that will look like:
```
SIPXCONFIG=# INSERT INTO users VALUES (nextval('user_seq'), 'Mihai', '123','321','Costache', 'MirceaMihai');
```

Note: **“nextval('user_seq')”** - This parameter is a **must** to increment the primary key used by “users” table.

We will run this command in devops style from ansible without first connecting to psql by adding a stored procedure and running it from ansible shell module. This will add superadmin permissions to superadmin user.

Below is the stored procedure content:
```
$ cat files/superadmin.sql
CREATE FUNCTION create_superadmin() RETURNS integer AS $$

DECLARE
    valueStorageId integer;  
BEGIN
   select nextval('storage_seq') into valueStorageId;
   INSERT INTO value_storage VALUES (valueStorageId);
   INSERT INTO setting_value VALUES (valueStorageId, 'ENABLE','permission/application/superadmin');
   INSERT INTO users VALUES (nextval('user_seq'), NULL, 'Ezuce123', 'Ezuce123', NULL, 'superadmin', valueStorageId, NULL, false, NULL, 'C', 'Ezuce123', true);
    RETURN 0;
END;
$$ LANGUAGE plpgsql;
select create_superadmin();
```

To execute this sql script we will add following lines in our playbook:
```
  - name: copy superadmin.sql function to remote machine
    copy: src="files/superadmin.sql"  dest="/tmp/superadmin.sql"
  - name: Execute psql script  
    shell: psql -U postgres SIPXCONFIG -f /tmp/superadmin.sql
  - name: Start services
    script: files/start_services.sh
```

**Step 2. Start services on remote server**

In order to start services on sipXcom server we need to create a script that will insert which services we want to start and then restart sipxconfig. You can check script content below

```
cat files/start_services.sh
#!/usr/bin/env bash

psql -U postgres SIPXCONFIG << EOF
INSERT INTO feature_global (feature_id) VALUES ('natTraversal');
INSERT INTO feature_global (feature_id) VALUES ('snmp');
INSERT INTO feature_global (feature_id) VALUES ('sipxlogwatcher');
INSERT INTO feature_global (feature_id) VALUES ('mail');
INSERT INTO feature_global (feature_id) VALUES ('ntpd');
INSERT INTO feature_global (feature_id) VALUES ('fail2ban');
INSERT INTO feature_global (feature_id) VALUES ('alarms');
INSERT INTO feature_local (feature_id, location_id) VALUES ('sipxdns', 1);
INSERT INTO feature_local (feature_id, location_id) VALUES ('systemaudit', 1);
INSERT INTO feature_local (feature_id, location_id) VALUES ('elasticsearch', 1);
INSERT INTO feature_local (feature_id, location_id) VALUES ('apache', 1);
INSERT INTO feature_local (feature_id, location_id) VALUES ('mongo', 1);
INSERT INTO feature_local (feature_id, location_id) VALUES ('phonelog', 1);
INSERT INTO feature_local (feature_id, location_id) VALUES ('ftp', 1);
INSERT INTO feature_local (feature_id, location_id) VALUES ('provision', 1);
INSERT INTO feature_local (feature_id, location_id) VALUES ('tftp', 1);
INSERT INTO feature_local (feature_id, location_id) VALUES ('freeSwitch', 1);
INSERT INTO feature_local (feature_id, location_id) VALUES ('ivr', 1);
INSERT INTO feature_local (feature_id, location_id) VALUES ('recording', 1);
INSERT INTO feature_local (feature_id, location_id) VALUES ('redis', 1);
INSERT INTO feature_local (feature_id, location_id) VALUES ('moh', 1);
INSERT INTO feature_local (feature_id, location_id) VALUES ('park', 1);
INSERT INTO feature_local (feature_id, location_id) VALUES ('registrar', 1);
INSERT INTO feature_local (feature_id, location_id) VALUES ('sipxcdr', 1);
INSERT INTO feature_local (feature_id, location_id) VALUES ('sipxsqa', 1);
INSERT INTO feature_local (feature_id, location_id) VALUES ('mwi', 1);
INSERT INTO feature_local (feature_id, location_id) VALUES ('proxy', 1);
INSERT INTO feature_local (feature_id, location_id) VALUES ('conference', 1);

EOF

service sipxconfig restart
```

**Step 3. Use Python to populate server with REST API**

To see all exposed REST API’s you can check this URL:
https://openuc.ezuce.com/sipxconfig/api/?_wadl


First we need to get json files with users, phones, gateways and dialplan to use. To do so I’ve used an already created machine.

To “pretty” visualize the output you need to use "| python -m json.tool" :
```
$ curl --insecure -XGET -u superadmin:Ezuce123 https://10.3.0.150/sipxconfig/api/rules/ -H "Content-type: application/json" | python -m json.tool
```

You can save this file in the required json format by running

```
$ curl --insecure -XGET -u superadmin:Ezuce123 https://10.3.0.150/sipxconfig/api/rules/ -H "Content-type: application/json" > users.json

```

Do the same for the rest of the API

Next we will create a python script that will iterate through the above json file, create an object and then POST it to API url:

```
$ cat files/add_users_API.py
#!/usr/bin/env python
import json, requests, yaml

output_json =  yaml.load(open('/var/log/users.json'))
headers = {'content-type': 'application/json'}
for i in output_json:
        
    for k in output_json[i]:
                        data=json.dumps(k,ensure_ascii=False)
                        new_data=data.encode("utf-8")
                       
                        r = requests.post("https://superadmin:Ezuce123@localhost/sipxconfig/api/users/", data=new_data,verify=False,headers=headers)
```

**Step 4. Bringing all together**

The following is a one step playbook that will be executed to start a configured and populated machine is presented next:

```
$ cat populated_sipxcom_final.yml
---
- hosts: localhost
  connection: local
  remote_user: devops
  gather_facts: no
  vars_files:
  - files/awscreds.yml
  - files/info_hosted.yml
  tasks:
  - name: Basic provisioning of EC2 instance
    ec2:
      aws_access_key: "{{ aws_id }}"
      aws_secret_key: "{{ aws_key }}"
      region: "{{ aws_region }}"
      image: "{{ sipxcom_ami }}"
      instance_type: "{{ large_instance }}"
      key_name: "{{ ssh_keyname }}"
      count: 1
      state: present
      group_id: "{{ secgroup_id }}"
      wait: yes
      vpc_subnet_id: subnet-29a32841
      assign_public_ip: yes
      instance_tags:
        Name: uc1.mihai.ezuce.ro
    register: ec2info
  - name: Print the results
    debug: var=ec2info
  - name: Add all instance public IPs to host group
    add_host: hostname={{ ec2info.instances[0].public_ip  }}
              groups=ec2hosts
              ansible_ssh_private_key_file=~/.ssh/devops-key.pem

              
  - name: Add Route 53 entries for newly created EC2 Instance
    route53:
      command: create
      zone: ezuce.ro
      overwrite: yes
      record: "{{ net_host }}.{{ net_domain }}"
      type: A
      ttl: 7200
      value: "{{ ec2info.instances[0].public_ip }}"
              
  - name: Add TCP SIP  SRV
    route53:
      command: create
      zone: ezuce.ro
      overwrite: yes
      record: "_sip._tcp.{{ net_domain }}."
      type: SRV
      value: "10 10 5060 {{ net_host }}.{{ net_domain }}"
     
              
  - name: Add UDP SIP  SRV
    route53:
      command: create
      zone: ezuce.ro
      overwrite: yes
      record: "_sip._udp.{{ net_domain }}."
      type: SRV
      value: "10 10 5060 {{ net_host }}.{{ net_domain }}"
 
  - name: Wait for SSH to come up
    remote_user: root
    wait_for: host={{ ec2info.instances[0].public_ip  }} port=22 delay=10 timeout=320 state=started


- hosts: ec2hosts
  vars_files:
      - files/awscreds.yml
      - files/info_hosted.yml
  remote_user: root
  tasks:
  - name: Configure sipxcom
    shell: sipxecs-setup --noui --sip_domain "{{ sip_domain }}" --sip_realm "{{ sip_realm }}" --net_domain "{{ net_domain }}" --net_host "{{ net_host }}"
  - name: copy superadmin.sql function to remote machine
    copy: src="files/superadmin.sql"  dest="/var/log/superadmin.sql"
  - name: Execute psql script  
    shell: psql -U postgres SIPXCONFIG -f /var/log/superadmin.sql
  - name: Start services
    script: files/start_services.sh
  - name: Install cURL for API
    yum: name=curl state=latest
  - name: Copy users.json
    copy: src="files/users.json" dest="/var/log/users.json"
  - name: Copy  phones.json
    copy: src="files/phones.json" dest="/var/log/phones.json"
  - name: Copy gateways.json
    copy: src="files/gateways.json" dest="/var/log/gateways.json"
  - name: Copy dialplan.json
    copy: src="files/dialplan.json" dest="/var/log/dialplan.json"
  - name: add users with API
    script: add_users_API.py
  - name: add phones with API
    script: add_phones_API.py
  - name: add gateways with API
    script: add_gateways_API.py
  - name: add dialplan with API
```

If you followed this series or articles these commands should be familiar to you. We have copied *.json files to EC2 /var/log path, after that we have executed *.py scripts that are momentarily hardcoded to execute using *.json files found in /var/log path.

Now we’re at the end of this series. You should have a fully functional sipXcom server just by running:

```
$ ansible-playbook populated_sipxcom_final.yml

----------------------------------------------------------------------------------

TASK [add users with API] ******************************************************
changed: [52.211.154.83]

TASK [add phones with API] *****************************************************
changed: [52.211.154.83]

TASK [add gateways with API] ***************************************************
changed: [52.211.154.83]

TASK [add dialplan with API] ***************************************************
changed: [52.211.154.83]

PLAY RECAP *********************************************************************
52.211.154.83              : ok=14   changed=13   unreachable=0    failed=0   
localhost                  : ok=7    changed=3    unreachable=0    failed=0   


```








