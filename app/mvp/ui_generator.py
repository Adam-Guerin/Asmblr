"""Advanced UI generator for creating seamless, conversion-optimized interfaces."""

import logging
from typing import Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class UIComponent:
    """Represents a UI component with its properties."""
    name: str
    component_type: str
    props: dict[str, Any]
    children: list['UIComponent'] = None
    styling: dict[str, Any] = None
    interactions: dict[str, Any] = None


class SeamlessUIGenerator:
    """Generates seamless, conversion-optimized UI components."""
    
    def __init__(self, config: dict[str, Any]):
        self.config = config
        self.design_tokens = self._initialize_design_tokens()
        self.conversion_patterns = self._initialize_conversion_patterns()
    
    def _initialize_design_tokens(self) -> dict[str, Any]:
        """Initialize consistent design tokens."""
        return {
            'spacing': {
                'xs': '4px', 'sm': '8px', 'md': '16px', 'lg': '24px',
                'xl': '32px', '2xl': '48px', '3xl': '64px', '4xl': '96px'
            },
            'typography': {
                'xs': '12px', 'sm': '14px', 'base': '16px', 'lg': '18px',
                'xl': '24px', '2xl': '32px', '3xl': '48px'
            },
            'colors': {
                'primary': {
                    '50': '#eff6ff', '500': '#3b82f6', '600': '#2563eb',
                    '700': '#1d4ed8', '900': '#1e3a8a'
                },
                'neutral': {
                    '50': '#f9fafb', '100': '#f3f4f6', '200': '#e5e7eb',
                    '500': '#6b7280', '700': '#374151', '900': '#111827'
                }
            },
            'border_radius': {
                'sm': '8px', 'md': '12px', 'lg': '16px', 'xl': '20px'
            },
            'shadows': {
                'subtle': '0 1px 2px 0 rgb(0 0 0 / 0.05)',
                'card': '0 4px 6px -1px rgb(0 0 0 / 0.1)',
                'floating': '0 10px 15px -3px rgb(0 0 0 / 0.1)',
                'modal': '0 25px 50px -12px rgb(0 0 0 / 0.25)'
            }
        }
    
    def _initialize_conversion_patterns(self) -> dict[str, Any]:
        """Initialize conversion-optimized UI patterns."""
        return {
            'hero_section': {
                'headline_max_chars': 60,
                'subheadline_max_chars': 120,
                'cta_placement': 'above_fold',
                'social_proof_position': 'below_headline',
                'value_proposition': 'benefit_focused'
            },
            'forms': {
                'max_fields': 5,
                'smart_defaults': True,
                'real_time_validation': True,
                'progressive_disclosure': True,
                'auto_save': True
            },
            'navigation': {
                'sticky_header': True,
                'breadcrumb_trail': True,
                'quick_actions': True,
                'search_instant': True,
                'mobile_bottom_nav': True
            },
            'social_proof': {
                'testimonial_format': 'face_name_result',
                'live_counters': True,
                'trust_badges': True,
                'success_metrics': True
            }
        }
    
    def generate_hero_section(self, product_data: dict[str, Any]) -> UIComponent:
        """Generate conversion-optimized hero section."""
        headline = self._optimize_headline(product_data.get('value_proposition', ''))
        subheadline = self._optimize_subheadline(product_data.get('description', ''))
        
        return UIComponent(
            name="HeroSection",
            component_type="layout",
            props={
                'className': 'relative bg-gradient-to-br from-blue-50 to-indigo-100 py-20 lg:py-32'
            },
            children=[
                UIComponent(
                    name="Container",
                    component_type="layout",
                    props={'className': 'max-w-7xl mx-auto px-4 sm:px-6 lg:px-8'},
                    children=[
                        UIComponent(
                            name="Grid",
                            component_type="layout",
                            props={'className': 'lg:grid lg:grid-cols-12 lg:gap-8 items-center'},
                            children=[
                                UIComponent(
                                    name="HeroContent",
                                    component_type="content",
                                    props={'className': 'lg:col-span-6'},
                                    children=[
                                        UIComponent(
                                            name="Headline",
                                            component_type="text",
                                            props={
                                                'className': 'text-4xl font-bold tracking-tight text-gray-900 sm:text-6xl',
                                                'children': headline
                                            }
                                        ),
                                        UIComponent(
                                            name="Subheadline",
                                            component_type="text",
                                            props={
                                                'className': 'mt-6 text-lg leading-8 text-gray-600',
                                                'children': subheadline
                                            }
                                        ),
                                        UIComponent(
                                            name="CTASection",
                                            component_type="actions",
                                            props={'className': 'mt-10 flex items-center gap-x-6'},
                                            children=[
                                                UIComponent(
                                                    name="PrimaryCTA",
                                                    component_type="button",
                                                    props={
                                                        'className': 'rounded-md bg-blue-600 px-3.5 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-blue-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600 transition-colors duration-200',
                                                        'children': product_data.get('primary_cta', 'Get Started')
                                                    }
                                                ),
                                                UIComponent(
                                                    name="SecondaryCTA",
                                                    component_type="link",
                                                    props={
                                                        'className': 'text-sm font-semibold leading-6 text-gray-900 hover:text-blue-600 transition-colors duration-200',
                                                        'children': product_data.get('secondary_cta', 'Learn more')
                                                    }
                                                )
                                            ]
                                        ),
                                        UIComponent(
                                            name="SocialProof",
                                            component_type="social_proof",
                                            props={'className': 'mt-8'},
                                            children=self._generate_social_proof(product_data)
                                        )
                                    ]
                                ),
                                UIComponent(
                                    name="HeroVisual",
                                    component_type="visual",
                                    props={'className': 'lg:col-span-6'},
                                    children=[
                                        UIComponent(
                                            name="ProductImage",
                                            component_type="image",
                                            props={
                                                'className': 'aspect-[6/5] w-full rounded-2xl object-cover shadow-2xl',
                                                'src': product_data.get('hero_image', '/api/placeholder/hero'),
                                                'alt': product_data.get('name', 'Product')
                                            }
                                        )
                                    ]
                                )
                            ]
                        )
                    ]
                )
            ]
        )
    
    def generate_seamless_form(self, form_config: dict[str, Any]) -> UIComponent:
        """Generate frictionless form with smart defaults."""
        return UIComponent(
            name="SeamlessForm",
            component_type="form",
            props={
                'className': 'space-y-6',
                'smartDefaults': True,
                'realTimeValidation': True
            },
            children=[
                UIComponent(
                    name="ProgressBar",
                    component_type="progress",
                    props={
                        'className': 'mb-6',
                        'steps': form_config.get('steps', ['Sign Up', 'Welcome'])
                    }
                ),
                *self._generate_form_fields(form_config.get('fields', [])),
                UIComponent(
                    name="FormActions",
                    component_type="actions",
                    props={'className': 'flex gap-4 pt-6'},
                    children=[
                        UIComponent(
                            name="SubmitButton",
                            component_type="button",
                            props={
                                'className': 'flex-1 rounded-md bg-blue-600 px-3.5 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-blue-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200',
                                'loading': True,
                                'children': form_config.get('submit_text', 'Get Started')
                            }
                        ),
                        UIComponent(
                            name="SkipButton",
                            component_type="button",
                            props={
                                'className': 'text-sm text-gray-500 hover:text-gray-700 transition-colors duration-200',
                                'variant': 'ghost',
                                'children': 'Skip for now'
                            }
                        )
                    ]
                )
            ]
        )
    
    def generate_conversion_dashboard(self, dashboard_data: dict[str, Any]) -> UIComponent:
        """Generate conversion-optimized dashboard."""
        return UIComponent(
            name="ConversionDashboard",
            component_type="layout",
            props={'className': 'min-h-screen bg-gray-50'},
            children=[
                self._generate_navigation(dashboard_data),
                UIComponent(
                    name="MainContent",
                    component_type="layout",
                    props={'className': 'lg:pl-72'},
                    children=[
                        self._generate_top_bar(dashboard_data),
                        UIComponent(
                            name="DashboardContent",
                            component_type="content",
                            props={'className': 'py-6'},
                            children=[
                                self._generate_welcome_section(dashboard_data),
                                self._generate_quick_actions(dashboard_data),
                                self._generate_metrics_grid(dashboard_data),
                                self._generate_activity_feed(dashboard_data)
                            ]
                        )
                    ]
                )
            ]
        )
    
    def _optimize_headline(self, value_prop: str) -> str:
        """Optimize headline for maximum conversion."""
        # Focus on benefits, not features
        benefit_keywords = ['save', 'increase', 'reduce', 'eliminate', 'achieve', 'unlock']
        
        # Keep under 60 characters
        if len(value_prop) > 60:
            value_prop = value_prop[:57] + '...'
        
        # Start with action verb if possible
        words = value_prop.split()
        if words and not any(word.lower() in benefit_keywords for word in words[:3]):
            # Add benefit focus
            value_prop = f"Unlock {value_prop.lower()}"
        
        return value_prop
    
    def _optimize_subheadline(self, description: str) -> str:
        """Optimize subheadline for clarity and trust."""
        # Keep under 120 characters
        if len(description) > 120:
            description = description[:117] + '...'
        
        # Add social proof element if possible
        if 'trusted' not in description.lower() and 'proven' not in description.lower():
            description = f"Trusted by thousands • {description}"
        
        return description
    
    def _generate_social_proof(self, product_data: dict[str, Any]) -> list[UIComponent]:
        """Generate social proof components."""
        return [
            UIComponent(
                name="TestimonialCarousel",
                component_type="social_proof",
                props={'className': 'mt-8'},
                children=[
                    UIComponent(
                        name="Testimonial",
                        component_type="testimonial",
                        props={
                            'className': 'flex items-center gap-x-6',
                            'avatar': '/api/placeholder/avatar',
                            'name': 'Sarah Chen',
                            'role': 'Product Manager',
                            'company': 'TechCorp',
                            'content': 'This transformed how we work. Saved 10+ hours per week.'
                        }
                    )
                ]
            ),
            UIComponent(
                name="TrustBadges",
                component_type="trust",
                props={'className': 'mt-6 flex items-center gap-x-6'},
                children=[
                    UIComponent(
                        name="SecurityBadge",
                        component_type="badge",
                        props={
                            'className': 'flex items-center gap-x-2 text-sm text-gray-600',
                            'icon': 'shield',
                            'text': 'SOC2 Compliant'
                        }
                    ),
                    UIComponent(
                        name="UserCount",
                        component_type="metric",
                        props={
                            'className': 'flex items-center gap-x-2 text-sm text-gray-600',
                            'icon': 'users',
                            'text': '10,000+ happy users'
                        }
                    )
                ]
            )
        ]
    
    def _generate_form_fields(self, fields: list[dict[str, Any]]) -> list[UIComponent]:
        """Generate optimized form fields."""
        form_fields = []
        
        for field in fields:
            field_component = UIComponent(
                name=field['name'].title(),
                component_type="input",
                props={
                    'className': 'block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-blue-600 sm:text-sm sm:leading-6 transition-all duration-200',
                    'type': field.get('type', 'text'),
                    'placeholder': field.get('placeholder', ''),
                    'defaultValue': field.get('default', ''),
                    'validation': field.get('validation', {}),
                    'smartDefault': field.get('smart_default', False)
                }
            )
            form_fields.append(field_component)
        
        return form_fields
    
    def _generate_navigation(self, dashboard_data: dict[str, Any]) -> UIComponent:
        """Generate seamless navigation."""
        return UIComponent(
            name="Navigation",
            component_type="navigation",
            props={
                'className': 'hidden lg:fixed lg:inset-y-0 lg:z-50 lg:flex lg:w-72 lg:flex-col',
                'sticky': True
            },
            children=[
                UIComponent(
                    name="Sidebar",
                    component_type="layout",
                    props={'className': 'flex grow flex-col gap-y-5 overflow-y-auto bg-white px-6 pb-4 ring-1 ring-gray-900/5'},
                    children=[
                        self._generate_logo_section(dashboard_data),
                        self._generate_nav_menu(dashboard_data),
                        self._generate_user_section(dashboard_data)
                    ]
                )
            ]
        )
    
    def _generate_top_bar(self, dashboard_data: dict[str, Any]) -> UIComponent:
        """Generate top navigation bar."""
        return UIComponent(
            name="TopBar",
            component_type="layout",
            props={
                'className': 'sticky top-0 z-40 lg:mx-auto lg:max-w-7xl lg:px-8 bg-white shadow-sm'
            },
            children=[
                UIComponent(
                    name="TopBarContent",
                    component_type="layout",
                    props={'className': 'flex h-16 items-center gap-x-4 px-4 sm:gap-x-6 sm:px-6 lg:px-0'},
                    children=[
                        UIComponent(
                            name="SearchBar",
                            component_type="search",
                            props={
                                'className': 'flex-1',
                                'placeholder': 'Search anything...',
                                'instant': True
                            }
                        ),
                        UIComponent(
                            name="Notifications",
                            component_type="notifications",
                            props={'className': 'relative'}
                        ),
                        UIComponent(
                            name="UserProfile",
                            component_type="profile",
                            props={'className': 'relative'}
                        )
                    ]
                )
            ]
        )
    
    def _generate_welcome_section(self, dashboard_data: dict[str, Any]) -> UIComponent:
        """Generate personalized welcome section."""
        return UIComponent(
            name="WelcomeSection",
            component_type="content",
            props={'className': 'px-4 sm:px-6 lg:px-8'},
            children=[
                UIComponent(
                    name="WelcomeMessage",
                    component_type="text",
                    props={
                        'className': 'text-2xl font-bold text-gray-900',
                        'children': f"Welcome back, {dashboard_data.get('user_name', 'User')}! 👋"
                    }
                ),
                UIComponent(
                    name="QuickStart",
                    component_type="text",
                    props={
                        'className': 'mt-2 text-sm text-gray-600',
                        'children': 'Here\'s what\'s happening with your account today.'
                    }
                )
            ]
        )
    
    def _generate_quick_actions(self, dashboard_data: dict[str, Any]) -> UIComponent:
        """Generate quick action buttons."""
        return UIComponent(
            name="QuickActions",
            component_type="actions",
            props={'className': 'px-4 sm:px-6 lg:px-8 mt-8'},
            children=[
                UIComponent(
                    name="ActionGrid",
                    component_type="layout",
                    props={'className': 'grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4'},
                    children=[
                        UIComponent(
                            name="ActionButton",
                            component_type="button",
                            props={
                                'className': 'relative overflow-hidden rounded-lg bg-white px-4 py-6 text-left shadow-sm hover:shadow-md transition-all duration-200 border border-gray-200',
                                'action': action['name']
                            }
                        ) for action in dashboard_data.get('quick_actions', [])
                    ]
                )
            ]
        )
    
    def _generate_metrics_grid(self, dashboard_data: dict[str, Any]) -> UIComponent:
        """Generate metrics display grid."""
        return UIComponent(
            name="MetricsGrid",
            component_type="metrics",
            props={'className': 'px-4 sm:px-6 lg:px-8 mt-8'},
            children=[
                UIComponent(
                    name="MetricCards",
                    component_type="layout",
                    props={'className': 'grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4'},
                    children=[
                        UIComponent(
                            name="MetricCard",
                            component_type="metric",
                            props={
                                'className': 'bg-white overflow-hidden rounded-lg shadow',
                                'metric': metric
                            }
                        ) for metric in dashboard_data.get('metrics', [])
                    ]
                )
            ]
        )
    
    def _generate_activity_feed(self, dashboard_data: dict[str, Any]) -> UIComponent:
        """Generate activity feed."""
        return UIComponent(
            name="ActivityFeed",
            component_type="feed",
            props={'className': 'px-4 sm:px-6 lg:px-8 mt-8'},
            children=[
                UIComponent(
                    name="ActivityList",
                    component_type="list",
                    props={'className': 'bg-white shadow rounded-lg'},
                    children=[
                        UIComponent(
                            name="ActivityItem",
                            component_type="list_item",
                            props={
                                'className': 'px-6 py-4 border-b border-gray-200 last:border-b-0',
                                'activity': activity
                            }
                        ) for activity in dashboard_data.get('recent_activity', [])
                    ]
                )
            ]
        )
    
    def _generate_logo_section(self, dashboard_data: dict[str, Any]) -> UIComponent:
        """Generate logo section."""
        return UIComponent(
            name="LogoSection",
            component_type="brand",
            props={'className': 'flex h-16 shrink-0 items-center'},
            children=[
                UIComponent(
                    name="Logo",
                    component_type="image",
                    props={
                        'className': 'h-8 w-auto',
                        'src': dashboard_data.get('logo', '/api/placeholder/logo'),
                        'alt': dashboard_data.get('company_name', 'Company')
                    }
                )
            ]
        )
    
    def _generate_nav_menu(self, dashboard_data: dict[str, Any]) -> UIComponent:
        """Generate navigation menu."""
        return UIComponent(
            name="NavMenu",
            component_type="navigation",
            props={'className': 'mt-6'},
            children=[
                UIComponent(
                    name="NavSection",
                    component_type="nav_section",
                    props={
                        'title': section['title'],
                        'items': section['items']
                    }
                ) for section in dashboard_data.get('navigation', [])
            ]
        )
    
    def _generate_user_section(self, dashboard_data: dict[str, Any]) -> UIComponent:
        """Generate user profile section."""
        return UIComponent(
            name="UserSection",
            component_type="user",
            props={'className': 'mt-auto'},
            children=[
                UIComponent(
                    name="UserProfileCard",
                    component_type="profile_card",
                    props={
                        'name': dashboard_data.get('user_name', 'User'),
                        'email': dashboard_data.get('user_email', 'user@example.com'),
                        'avatar': dashboard_data.get('user_avatar', '/api/placeholder/avatar')
                    }
                )
            ]
        )
    
    def generate_component_code(self, component: UIComponent) -> str:
        """Generate React/TypeScript code for a component."""
        if component.component_type == "layout":
            return self._generate_layout_code(component)
        elif component.component_type == "button":
            return self._generate_button_code(component)
        elif component.component_type == "form":
            return self._generate_form_code(component)
        elif component.component_type == "text":
            return self._generate_text_code(component)
        else:
            return self._generate_generic_code(component)
    
    def _generate_layout_code(self, component: UIComponent) -> str:
        """Generate layout component code."""
        children_code = ""
        if component.children:
            children_code = "\n".join([self.generate_component_code(child) for child in component.children])
        
        return f"""
export function {component.name}() {{
  return (
    <div className="{component.props.get('className', '')}">
      {children_code}
    </div>
  )
}}
"""
    
    def _generate_button_code(self, component: UIComponent) -> str:
        """Generate button component code with micro-interactions."""
        return f"""
import {{ motion }} from 'framer-motion'

export function {component.name}() {{
  return (
    <motion.button
      className="{component.props.get('className', '')}"
      whileHover={{{{ scale: 1.02 }}}}
      whileTap={{{{ scale: 0.98 }}}}
      transition={{{{ duration: 0.15 }}}}
    >
      {component.props.get('children', '')}
    </motion.button>
  )
}}
"""
    
    def _generate_form_code(self, component: UIComponent) -> str:
        """Generate form component with validation."""
        children_code = ""
        if component.children:
            children_code = "\n".join([self.generate_component_code(child) for child in component.children])
        
        return f"""
import {{ useForm }} from 'react-hook-form'
import {{ zodResolver }} from '@hookform/resolvers/zod'
import {{ z }} from 'zod'

export function {component.name}() {{
  const form = useForm({{
    resolver: zodResolver(z.object({{
      /* schema here */
    }})),
    defaultValues: {{{{ /* smart defaults */ }}}}
  }})
  
  return (
    <form onSubmit={{form.handleSubmit(/* submit handler */)}} className="{component.props.get('className', '')}">
      {children_code}
    </form>
  )
}}
"""
    
    def _generate_text_code(self, component: UIComponent) -> str:
        """Generate text component code."""
        tag = "p" if "text" in component.props.get('className', '') else "h1"
        return f'<{tag} className="{component.props.get("className", "")}">{component.props.get("children", "")}</{tag}>'
    
    def _generate_generic_code(self, component: UIComponent) -> str:
        """Generate generic component code."""
        return f"""
export function {component.name}() {{
  return (
    <div className="{component.props.get('className', '')}">
      {component.props.get('children', '')}
    </div>
  )
}}
"""
