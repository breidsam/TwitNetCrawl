from load_and_write_files import *



def update_search_params(user, network, value):

    users_to_search = load_accounts_for_analysis()
    if user[0].lower() in users_to_search: # removing current user from searchlist
        users_to_search.pop(user[0].lower())
    add_to_solved_tasks(user[0].lower())
    relevance_dict = update_relevance_dict(network, value, users_to_search)
    write_accounts_for_analysis(relevance_dict)
    relevance_list = list(reversed(sorted(relevance_dict.items(), key=operator.itemgetter(1))))

    return relevance_list



def update_relevance_dict(network, value, relevant_users):

    new_relevant_users = [(user, value * network[user]) for user in network] # ersetzt determine relevance - Funktion
    solved_tasks = load_solved_tasks()
    for new_user in new_relevant_users:
        if new_user[0].lower() in solved_tasks:
            if new_user[0].lower() in relevant_users:
                relevant_users.pop(new_user[0].lower())
            continue # jump to next new_user
        else:
            if new_user[0].lower() not in relevant_users:
                relevant_users.update({new_user[0].lower(): new_user[1]})
            else:
                value = relevant_users[new_user[0].lower()] + new_user[1]
                relevant_users[new_user[0].lower()]= value

    return relevant_users


def load_accounts_for_analysis():
    return load_json('config/accounts_for_analysis')['accounts']

def write_accounts_for_analysis(data):
    write_json({"accounts": data}, 'config/accounts_for_analysis')


def load_search_queue():
    data = load_accounts_for_analysis()
    sorted_data = list(reversed(sorted(data.items(), key=operator.itemgetter(1))))
    return sorted_data

