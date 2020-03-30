import twint
import tweepy
from tweepy_config import get_tweepy_api
from collections import Counter
from relevance import update_search_params, load_search_queue, load_accounts_for_analysis
import time
from load_and_write_files import load_solved_tasks, write_json, save_exception

count_all = Counter()
tweepy_api = get_tweepy_api()

# Get user-object for basic information

def get_user(user_tuple):
    while True:
        try:
            user = (tweepy_api.get_user(screen_name=user_tuple[0]))._json
            return user
        except Exception as e:
            if str(e) == "[{'code': 50, 'message': 'User not found.'}]": # profile is deleted
                return False
            if str(e) == "[{'code': 63, 'message': 'User has been suspended.'}]": # profile is temporaly suspended
                return False
            else:
                time.sleep(1)
            save_exception(user_tuple[0], ' get_user', str(e))
            print(e)
            
# Get all profiles followed by the account

def get_followings(username, timeout=360, sleep=30):
    start = time.time()
    c = twint.Config()
    c.Username = username
    c.Store_object = True
    c.Hide_output = True
    #c.Limit = 150
    #c.Count = True
    while True:
        try:
            twint.run.Following(c)
            followings = twint.output.follows_list
            following_names = [f.lower() for f in followings]
            followings.clear()
            if len(following_names) > 0:
                return following_names
            else:
                remaining = timeout - (time.time() - start)
                if remaining > 0:
                    print("---- Didn't get any followings, timeout in {} seconds".format(int(remaining)))
                    time.sleep(sleep)
                else:
                    return []
        except Exception as e:
            save_exception(username, 'get_followings', str(e))
            print(e)
            time.sleep(1)

# Getting statuses from usertimeline

def get_retweeted_users(username, followings):
    while True:
        try:
            statuses = [
                            s for s in tweepy.Cursor(
                                                        tweepy_api.user_timeline,
                                                        screen_name=username, count=100,
                                                        tweet_mode='extended', retweet_mode='extended').items()
            ]
            break
        except Exception as e:
            if str(e) == 'Twitter error response: status code = 401': # user profile is locked
                usr_statuses = {'error': 'locked profile'}
                retw_foll_usrs = []
                return retw_foll_usrs, usr_statuses
            else:
                time.sleep(1)
            save_exception(username, 'get_retweeted_users', str(e))
            print(e)

    usr_statuses = {}
    retw_foll_usrs = []

    # Storing all statuses to userdata and adding all retweeted users who are followed
    for s in statuses:
        usr_statuses.update({s._json['id']: s._json})
        if 'retweeted_status' in s._json.keys() and s.retweeted_status.user.screen_name.lower() in followings:
            retw_foll_usrs.append(s.retweeted_status.user.screen_name.lower())


    return retw_foll_usrs, usr_statuses

# Get all favored tweets

def get_favored_users(username, user_id, followings, limit=100):
    while True:
        try:
            statuses = [s for s in tweepy.Cursor(tweepy_api.favorites, id=user_id,
                                                result_type="recent", tweet_mode="extended",
                                                retweet_mode='extended', count=limit).items()]
            break

        except Exception as e:
            if str(e) == 'Twitter error response: status code = 401': # user profile is locked
                favs = {'error': 'locked profile'}
                favored_users = []
                return favored_users, favs
            else:
                time.sleep(1)    
            save_exception(username, 'get_favored_users', str(e))
            print(e)
            


    favs = {}
    favored_users = []

    for s in statuses:
        favs.update({s._json["id"]: s._json})
        followings_low = [user.lower() for user in followings]

    # select users who are favored and followed
    for f in favs.values():
        if f['user']['screen_name'].lower() in followings_low:
            favored_users.append(f['user']['screen_name'].lower())

    return favored_users, favs

# calculate sum of all retweets and favs for one account

def calculate_score(retw_foll_usrs, fav_foll_usrs):
    count_all.update(retw_foll_usrs)
    result_retweets = count_all.most_common()
    count_all.clear()

    count_all.update(fav_foll_usrs)
    result_favored = count_all.most_common()
    count_all.clear()
    scores = []
    for user_a in result_retweets:
        for user_b in result_favored:
            if user_a[0].lower() == user_b[0].lower():
                value = user_a[1] + user_b[1]
                scores.append((user_a[0], value / 3000))
    return scores


def check_friendship(user_tuple, other_user):

    try:
        friendship = tweepy_api.show_friendship(source_screen_name=other_user[0], target_screen_name=user_tuple[0])
        if friendship[0].following:
            return True
        else:
            return False
    except Exception as e:
        save_exception(user_tuple[0], 'check_friendship', str(e))
        print(e)
        #if e == [{'code': 163, 'message': 'Could not determine source user.'}]:
        #    return False

        return False

def get_network(user_tuple, number):
    
    print('##############'
          '\n## Searching network of {}'.format(user_tuple[0])
          )

    json_data = {'user': None, 'value': None, 'network': None, 'followings': None, 'tweets': None,
                'favs': None}
    filename = 'Data/' + str(number) + '_' + user_tuple[0]

    user = get_user(user_tuple)

    if user:
        user_id = user['id']

        # Get all followed users
        following_names = get_followings(user_tuple[0])
        print("## {} followed accounts".format(len(following_names)))

        # Get all users who have been retweeted and followed
        retw_foll_usrs, usr_statuses = get_retweeted_users(user_tuple[0], following_names)
        print("## {} statuses\n## {} retweets from followed users".format(len(usr_statuses), len(retw_foll_usrs)))

        # Get all data for favored users and a list of favored and followed users
        fav_foll_usrs, fav_usrs = get_favored_users(user_tuple[0], user_id, following_names)
        print("## {} favored tweets\n## {} favored tweets from followed users".format(len(fav_usrs),
                                                                                 len(fav_foll_usrs)))
        scores = calculate_score(retw_foll_usrs, fav_foll_usrs)

        network = []
        network_dicts = {}

        for other_user in scores:
            if check_friendship(user_tuple, other_user):
                network.append(other_user)
                network_dicts.update({other_user[0].lower(): other_user[1]})

        print("## {} accounts scored".format(len(scores)))
        print("## {} added to network".format(len(network_dicts)))

        # writing collected data to userfile:
        json_data['user'] = user
        json_data['value'] = user_tuple[1]
        json_data['network'] = network_dicts
        json_data['followings'] = following_names
        json_data['tweets'] = usr_statuses
        json_data['favs'] = fav_usrs
    else:
        json_data['user'] = {'error': 'account deleted or suspended'}
        json_data['value'] = user_tuple[1]
        json_data['network'] = {}
        json_data['followings'] = []
        json_data['tweets'] = {}
        json_data['favs'] = {}
    print('## saving data...')
    write_json(json_data, filename)
    
    return json_data
    #return reversed(sorted(network, key=lambda x: x[1]))


def analyse_network(username):
    count = 1
    search_queue = load_search_queue()

    if len(search_queue) > 0:
        user = search_queue[0]
    else:
        user = (username, 1) # first user gets score of 1

    while True:
        if user[0].lower() not in load_solved_tasks():
            
            network = get_network(user, count)
            relevance_list = update_search_params(user, network['network'], network['value'])

            print("Account {}---> {} accounts in search queue\n".format(count, len(relevance_list)))
            if len(relevance_list) > 0:
                user = relevance_list[0]
            else:
                break
            count += 1
        else:
            break
    print("\nNo more users in list. Finishing search ")
    return

