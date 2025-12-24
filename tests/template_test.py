#!/usr/bin/env python3
"""
Test template expressions with correct user data structure.
"""

from jinja2 import Template

# Test user data structure matching the current UserProfileManager schema
test_user = {
    'username': 'testuser',
    'email': 'test@example.com',
    'preferences': {
        'food_restrictions': ['vegetarian', 'no_spicy'],
        'interests': ['k-pop', 'temples'],
        'cultural_preferences': ['traditional', 'modern'],
        'budget_range': 'mid-range',
        'travel_style': 'solo'
    },
    'history': {
        'visited_places': [
            {'name': 'Gyeongbokgung Palace', 'visited_date': '2023-01-01'},
            {'name': 'Bukchon Hanok Village', 'visited_date': '2023-01-02'}
        ],
        'favorites': [
            {'name': 'Korean BBQ', 'category': 'restaurant'},
            {'name': 'Hongdae Nightlife', 'category': 'entertainment'}
        ]
    }
}

def test_template_expressions():
    """Test template expressions used in the updated templates."""
    expressions = [
        ('Visited places count', 'user.get("history", {}).get("visited_places", [])|length'),
        ('Favorites count', 'user.get("history", {}).get("favorites", [])|length'),
        ('Food restrictions', 'user.get("preferences", {}).get("food_restrictions", [])|join(", ")'),
        ('Budget range', 'user.get("preferences", {}).get("budget_range")'),
        ('Travel style', 'user.get("preferences", {}).get("travel_style")'),
        ('Cultural preferences', 'user.get("preferences", {}).get("cultural_preferences", [])|join(", ")'),
        ('Interests', 'user.get("preferences", {}).get("interests", [])|join(", ")'),
    ]
    
    print("Testing template expressions:")
    print("=" * 50)
    
    all_passed = True
    for name, expr in expressions:
        try:
            template = Template('{{ ' + expr + ' }}')
            result = template.render(user=test_user)
            print(f"✅ {name}: {result}")
        except Exception as e:
            print(f"❌ {name}: ERROR - {e}")
            all_passed = False
    
    print("=" * 50)
    if all_passed:
        print("✅ All template expressions work correctly!")
        return True
    else:
        print("❌ Some template expressions failed!")
        return False

def test_conditional_expressions():
    """Test conditional expressions used in templates."""
    conditionals = [
        ('Has visited places', 'user.get("history", {}).get("visited_places")'),
        ('Has favorites', 'user.get("history", {}).get("favorites")'),
        ('Budget range selected', 'user.get("preferences", {}).get("budget_range") == "mid-range"'),
    ]
    
    print("\nTesting conditional expressions:")
    print("=" * 50)
    
    all_passed = True
    for name, expr in conditionals:
        try:
            template = Template('{% if ' + expr + ' %}True{% else %}False{% endif %}')
            result = template.render(user=test_user)
            print(f"✅ {name}: {result}")
        except Exception as e:
            print(f"❌ {name}: ERROR - {e}")
            all_passed = False
    
    print("=" * 50)
    return all_passed

if __name__ == '__main__':
    success1 = test_template_expressions()
    success2 = test_conditional_expressions()
    
    if success1 and success2:
        print("\n🎉 All template tests passed! Templates are ready to use.")
        exit(0)
    else:
        print("\n💥 Some template tests failed! Check the expressions.")
        exit(1)