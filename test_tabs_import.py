# Test script to import dashboard and call tab creation functions
from dashboard import create_insights_tab, create_action_tab, create_profile_tab

if __name__ == '__main__':
    print('Testing insight tab...')
    insights = create_insights_tab()
    print('Insights tab created:', type(insights))
    print()

    print('Testing action tab...')
    action = create_action_tab()
    print('Action tab created:', type(action))
    print()

    print('Testing profile tab...')
    profile = create_profile_tab()
    print('Profile tab created:', type(profile))
