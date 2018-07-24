import os


if __name__ == "__main__":
    mv_dir = 'moviedata'
    if not os.path.exists(mv_dir):
        os.makedir(mv_dir)
        print("Created moviedata directory.")

    lists_dir = 'lists'
    if not os.path.exists(lists_dir):
        os.makedir(lists_dir)
        print("Created lists directory.\n")

    user_dir = 'user'
    if not os.path.exists(user_dir):
        os.makedir(user_dir)
        print("Created user directory.\n")

    ufile = 'your_username.txt'
    if not os.path.isfile(ufile):
        user = input("Please tell me your username on Letterboxd:\n")
        with open(ufile, 'w') as uf:
            uf.write(user)
        print("Great, {} is set as default now.".format(user))
    else:
        dec = input("Do you want to change the default user? (y/n)\n")
        if dec == "y":
            new_user = input("Please tell me a username on Letterboxd:\n")
            with open(ufile, 'w') as uw:
                uw.write(new_user)
        else:
            print("Username is still {}.".format(open(ufile, 'r').read()))
