import React, { useState, useEffect } from 'react';
import axios from 'axios';
import ReactMarkdown from 'react-markdown';
import { Message, WeeklyPlanDay } from '../types';
import { ChatInput } from './ChatInput';
import { MessageDisplay } from './MessageDisplay';

// API base URL - use relative URL in production or absolute URL in development
const API_BASE_URL = process.env.NODE_ENV === 'production' 
  ? '/api' // In production, use relative path (served by same domain)
  : 'http://localhost:9000/api'; // In development, use explicit host

interface AssessmentFlowProps {
  onComplete: (lesson: any, messages: Message[]) => void;
  onCancel: () => void;
}

interface UserProfile {
  english_level: string;
  interests: string[];
  learning_goals: string[];
  study_time_per_day: number;
  total_study_day: number;
}

interface TotalPlan {
  topics: {
    day_number: number;
    topic: string;
    description: string;
  }[];
}

export const AssessmentFlow: React.FC<AssessmentFlowProps> = ({ onComplete, onCancel }) => {
  // Current step in the assessment flow
  const [currentStep, setCurrentStep] = useState<1 | 2 | 3 | 4>(1);
  
  // Chat messages for the initial assessment
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  
  // Data from each step
  const [userProfile, setUserProfile] = useState<UserProfile | null>(null);
  const [totalPlan, setTotalPlan] = useState<TotalPlan | null>(null);
  const [selectedTopic, setSelectedTopic] = useState<number | null>(null);
  const [weeklyPlan, setWeeklyPlan] = useState<WeeklyPlanDay[] | null>(null);
  
  // UI states
  const [isLoading, setIsLoading] = useState(false);
  const [loadingStatus, setLoadingStatus] = useState('');
  const [error, setError] = useState<string | null>(null);
  
  // Initialize the assessment
  useEffect(() => {
    if (currentStep === 1 && messages.length === 0) {
      startInitialAssessment();
    }
  }, []);

  // Start the initial assessment chat
  const startInitialAssessment = async () => {
    try {
      setIsLoading(true);
      setLoadingStatus('正在准备评估...');
      const initialMessage: Message = {
        role: 'user' as const,
        content: 'Hello, I would like to improve my English. Can you help me assess my current level?'
      };
      
      const response = await axios.post(`${API_BASE_URL}/assessment/initial-chat`, [initialMessage]);

      const assistantMessage: Message = {
        role: 'assistant' as const,
        content: response.data.content || response.data
      };
      setMessages([initialMessage, assistantMessage]);

      // Check if assessment is already complete
      if (assistantMessage.content.includes('<ASSESSMENT_COMPLETE>')) {
        await analyzeProfile([initialMessage, assistantMessage]);
      }
    } catch (error) {
      console.error('Error starting assessment:', error);
      setError('Failed to start assessment. Please try again.');
    } finally {
      setIsLoading(false);
      setLoadingStatus('');
    }
  };

  // Send a message in the chat
  const sendMessage = async () => {
    if (!input.trim() || isLoading) return;

    try {
      setIsLoading(true);
      const userMessage: Message = { role: 'user', content: input };
      
      // Add user message immediately
      const updatedMessages = [...messages, userMessage];
      setMessages(updatedMessages);
      setInput('');
      
      // Use assessment API endpoint
      const response = await axios.post(
        `${API_BASE_URL}/assessment/initial-chat`,
        updatedMessages
      );
      
      // Handle assessment response
      const assistantMessage: Message = {
        role: 'assistant',
        content: response.data.content || response.data
      };
      
      const newMessages = [...updatedMessages, assistantMessage];
      setMessages(newMessages);
      
      // Check if assessment is complete
      if (assistantMessage.content.includes('<ASSESSMENT_COMPLETE>')) {
        // Save conversation to localStorage for persistence
        localStorage.setItem('assessment_conversation', JSON.stringify(newMessages));
        
        // Move to profile analysis
        await analyzeProfile(newMessages);
      }
    } catch (error) {
      console.error('Error sending message:', error);
      setError('Failed to send message. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  // Step 2: Analyze the conversation to generate user profile
  const analyzeProfile = async (conversationMessages: Message[]) => {
    try {
      setCurrentStep(2);
      setLoadingStatus('正在分析对话内容...');
      setIsLoading(true);
      
      // Analyze conversation to generate user profile
      const profileResponse = await axios.post(`${API_BASE_URL}/assessment/analyze-profile`, conversationMessages);
      const profile = profileResponse.data;
      
      // Save profile to state and localStorage
      setUserProfile(profile);
      localStorage.setItem('user_profile', JSON.stringify(profile));
      setIsLoading(false);
      
      // Don't automatically proceed to next step - user needs to review profile first
    } catch (error) {
      console.error('Error analyzing profile:', error);
      setError('Failed to analyze your profile. Please try again.');
      setIsLoading(false);
    }
  };

  // Step 3: Generate total learning plan
  const generateTotalPlan = async (profile: UserProfile) => {
    try {
      setCurrentStep(3);
      setLoadingStatus('正在生成学习计划...');
      
      // Generate total plan using user profile
      const totalPlanResponse = await axios.post(`${API_BASE_URL}/assessment/generate-total-plan`, profile);
      const plan = totalPlanResponse.data;
      
      // Save plan to state and localStorage
      setTotalPlan(plan);
      localStorage.setItem('total_plan', JSON.stringify(plan));
      setIsLoading(false);
      
      // Don't automatically proceed to next step - user needs to select a topic
    } catch (error) {
      console.error('Error generating total plan:', error);
      setError('Failed to generate learning plan. Please try again.');
      setIsLoading(false);
    }
  };

  // Handle topic selection and generate weekly plan
  const handleTopicSelection = async (dayNumber: number) => {
    try {
      setSelectedTopic(dayNumber);
      setCurrentStep(4);
      setLoadingStatus('正在生成每周学习计划...');
      setIsLoading(true);
      
      if (!userProfile) {
        throw new Error('User profile is missing');
      }
      
      // Combine selected topic with user profile
      const topicWithProfile = {
        ...userProfile,
        selected_day: dayNumber
      };
      
      // Generate weekly plan
      const weeklyPlanResponse = await axios.post(`${API_BASE_URL}/assessment/generate-weekly-plan`, topicWithProfile);
      const weeklyPlan = weeklyPlanResponse.data;
      
      // Save weekly plan to state and localStorage
      setWeeklyPlan(weeklyPlan);
      localStorage.setItem('weekly_plan', JSON.stringify(weeklyPlan));
      
      // Create a lesson based on the weekly plan
      const firstDay = weeklyPlan[0];
      const studyLesson = {
        mode: 'study',
        topic: `English Learning for ${userProfile.english_level.charAt(0).toUpperCase() + userProfile.english_level.slice(1)} Level`,
        speechText: `Welcome to your personalized English learning journey! Based on your ${userProfile.english_level} level and interests in ${userProfile.interests.join(', ')}, we've created a custom plan for you.`,
        knowledge_points: firstDay.knowledge_points,
        displayText: `# Your Personalized English Learning Plan\n\n## Based on Your Profile:\n- Level: ${userProfile.english_level}\n- Interests: ${userProfile.interests.join(', ')}\n- Goals: ${userProfile.learning_goals.join(', ')}\n- Daily study time: ${userProfile.study_time_per_day} minutes\n\n## This Week's Focus:\n${weeklyPlan.map((day: WeeklyPlanDay) => `### Day ${day.day_number}: ${day.topic}`).join('\n')}`,
        materials: firstDay.materials,
        review_activities: firstDay.review_activities,
        estimated_time: firstDay.estimated_time
      };
      
      // Complete the assessment flow
      onComplete(studyLesson, messages);
    } catch (error) {
      console.error('Error generating weekly plan:', error);
      setError('Failed to generate weekly plan. Please try again.');
      setIsLoading(false);
    }
  };

  // Handle manual edits to the user profile
  const handleProfileEdit = (updatedProfile: UserProfile) => {
    setUserProfile(updatedProfile);
    localStorage.setItem('user_profile', JSON.stringify(updatedProfile));
    // Regenerate the total plan with updated profile
    generateTotalPlan(updatedProfile);
  };

  // Render different content based on current step
  const renderStepContent = () => {
    switch (currentStep) {
      case 1: // Initial chat assessment
        return (
          <div className="flex flex-col h-full">
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
              {messages.map((message, index) => (
                <MessageDisplay key={index} message={message} />
              ))}
              {isLoading && messages.length === 0 && (
                <div className="flex justify-center items-center h-full">
                  <div className="animate-spin h-8 w-8 border-4 border-blue-500 border-t-transparent rounded-full"></div>
                  <span className="ml-2 text-gray-600">{loadingStatus || 'Loading...'}</span>
                </div>
              )}
            </div>
            <ChatInput
              input={input}
              setInput={setInput}
              sendMessage={sendMessage}
              isLoading={isLoading}
            />
          </div>
        );
        
      case 2: // Profile analysis result
        return (
          <div className="p-6 space-y-6">
            <h2 className="text-2xl font-bold text-blue-800">Your English Learning Profile</h2>
            {userProfile ? (
              <div className="bg-white p-6 rounded-lg shadow-md">
                <div className="space-y-4">
                  <div>
                    <h3 className="text-lg font-semibold">English Level</h3>
                    <select 
                      className="mt-1 block w-full p-2 border border-gray-300 rounded-md" 
                      value={userProfile.english_level}
                      onChange={(e) => handleProfileEdit({...userProfile, english_level: e.target.value})}
                    >
                      <option value="none">None - Complete beginner</option>
                      <option value="beginner">Beginner</option>
                      <option value="intermediate">Intermediate</option>
                      <option value="advanced">Advanced</option>
                    </select>
                  </div>
                  
                  <div>
                    <h3 className="text-lg font-semibold">Interests</h3>
                    <div className="flex flex-wrap gap-2 mt-1">
                      {userProfile.interests.map((interest, index) => (
                        <div key={index} className="bg-blue-100 px-3 py-1 rounded-full flex items-center">
                          <span>{interest}</span>
                          <button 
                            className="ml-2 text-red-500"
                            onClick={() => {
                              const newInterests = [...userProfile.interests];
                              newInterests.splice(index, 1);
                              handleProfileEdit({...userProfile, interests: newInterests});
                            }}
                          >
                            ×
                          </button>
                        </div>
                      ))}
                      <input 
                        className="border border-gray-300 px-3 py-1 rounded-full"
                        placeholder="Add interest..."
                        onKeyPress={(e) => {
                          if (e.key === 'Enter' && e.currentTarget.value.trim()) {
                            handleProfileEdit({
                              ...userProfile, 
                              interests: [...userProfile.interests, e.currentTarget.value.trim()]
                            });
                            e.currentTarget.value = '';
                          }
                        }}
                      />
                    </div>
                  </div>
                  
                  <div>
                    <h3 className="text-lg font-semibold">Learning Goals</h3>
                    <div className="flex flex-wrap gap-2 mt-1">
                      {userProfile.learning_goals.map((goal, index) => (
                        <div key={index} className="bg-green-100 px-3 py-1 rounded-full flex items-center">
                          <span>{goal}</span>
                          <button 
                            className="ml-2 text-red-500"
                            onClick={() => {
                              const newGoals = [...userProfile.learning_goals];
                              newGoals.splice(index, 1);
                              handleProfileEdit({...userProfile, learning_goals: newGoals});
                            }}
                          >
                            ×
                          </button>
                        </div>
                      ))}
                      <input 
                        className="border border-gray-300 px-3 py-1 rounded-full"
                        placeholder="Add goal..."
                        onKeyPress={(e) => {
                          if (e.key === 'Enter' && e.currentTarget.value.trim()) {
                            handleProfileEdit({
                              ...userProfile, 
                              learning_goals: [...userProfile.learning_goals, e.currentTarget.value.trim()]
                            });
                            e.currentTarget.value = '';
                          }
                        }}
                      />
                    </div>
                  </div>
                  
                  <div>
                    <h3 className="text-lg font-semibold">Daily Study Time (minutes)</h3>
                    <input 
                      type="number" 
                      className="mt-1 block w-full p-2 border border-gray-300 rounded-md"
                      value={userProfile.study_time_per_day}
                      onChange={(e) => handleProfileEdit({...userProfile, study_time_per_day: parseInt(e.target.value) || 30})}
                      min="5"
                      max="240"
                    />
                  </div>
                  
                  <div>
                    <h3 className="text-lg font-semibold">Total Study Days</h3>
                    <input 
                      type="number" 
                      className="mt-1 block w-full p-2 border border-gray-300 rounded-md"
                      value={userProfile.total_study_day}
                      onChange={(e) => handleProfileEdit({...userProfile, total_study_day: parseInt(e.target.value) || 30})}
                      min="7"
                      max="365"
                    />
                  </div>
                </div>
                
                <div className="mt-6 flex justify-between">
                  <button
                    onClick={() => setCurrentStep(1)}
                    className="px-4 py-2 bg-gray-300 text-gray-800 rounded-md hover:bg-gray-400 transition-colors"
                  >
                    Back to Chat
                  </button>
                  <button
                    onClick={() => generateTotalPlan(userProfile)}
                    className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
                  >
                    Generate Learning Plan
                  </button>
                </div>
              </div>
            ) : (
              <div className="flex justify-center items-center h-64">
                <div className="animate-spin h-8 w-8 border-4 border-blue-500 border-t-transparent rounded-full"></div>
                <span className="ml-2 text-gray-600">{loadingStatus || 'Analyzing your profile...'}</span>
              </div>
            )}
            {error && (
              <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mt-4">
                {error}
              </div>
            )}
          </div>
        );
        
      case 3: // Total plan with topic selection
        return (
          <div className="p-6 space-y-6">
            <h2 className="text-2xl font-bold text-blue-800">Your Learning Plan</h2>
            {totalPlan ? (
              <div className="bg-white p-6 rounded-lg shadow-md">
                <div className="mb-6">
                  <h3 className="text-lg font-semibold mb-2">Your Profile Summary</h3>
                  {userProfile && (
                    <div className="bg-blue-50 p-4 rounded-md">
                      <p><strong>Level:</strong> {userProfile.english_level}</p>
                      <p><strong>Interests:</strong> {userProfile.interests.join(', ')}</p>
                      <p><strong>Goals:</strong> {userProfile.learning_goals.join(', ')}</p>
                      <p><strong>Daily study time:</strong> {userProfile.study_time_per_day} minutes</p>
                      <p><strong>Total study days:</strong> {userProfile.total_study_day} days</p>
                    </div>
                  )}
                </div>
                
                <h3 className="text-lg font-semibold mb-4">Select a Topic to Start With</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {totalPlan.topics.map((topic) => (
                    <div 
                      key={topic.day_number}
                      className="border border-gray-200 rounded-lg p-4 cursor-pointer hover:bg-blue-50 transition-colors"
                      onClick={() => handleTopicSelection(topic.day_number)}
                    >
                      <h4 className="font-medium text-blue-800">Day {topic.day_number}: {topic.topic}</h4>
                      <p className="text-gray-600 mt-2">{topic.description}</p>
                    </div>
                  ))}
                </div>
                
                <div className="mt-6 flex justify-between">
                  <button
                    onClick={() => setCurrentStep(2)}
                    className="px-4 py-2 bg-gray-300 text-gray-800 rounded-md hover:bg-gray-400 transition-colors"
                  >
                    Back to Profile
                  </button>
                </div>
              </div>
            ) : (
              <div className="flex justify-center items-center h-64">
                <div className="animate-spin h-8 w-8 border-4 border-blue-500 border-t-transparent rounded-full"></div>
                <span className="ml-2 text-gray-600">{loadingStatus || 'Generating learning plan...'}</span>
              </div>
            )}
            {error && (
              <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mt-4">
                {error}
              </div>
            )}
          </div>
        );
        
      case 4: // Weekly plan generation
        return (
          <div className="p-6 space-y-6">
            <h2 className="text-2xl font-bold text-blue-800">Generating Your Weekly Plan</h2>
            <div className="flex justify-center items-center h-64">
              <div className="animate-spin h-8 w-8 border-4 border-blue-500 border-t-transparent rounded-full"></div>
              <span className="ml-2 text-gray-600">{loadingStatus || 'Creating your personalized weekly plan...'}</span>
            </div>
            {error && (
              <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mt-4">
                {error}
                <button
                  onClick={() => setCurrentStep(3)}
                  className="mt-2 px-4 py-2 bg-red-200 text-red-800 rounded-md hover:bg-red-300 transition-colors"
                >
                  Go Back
                </button>
              </div>
            )}
          </div>
        );
        
      default:
        return null;
    }
  };

  // Render step indicator
  const renderStepIndicator = () => {
    return (
      <div className="flex justify-between items-center mb-8 px-6 pt-6">
        {[1, 2, 3, 4].map((step) => (
          <div key={step} className="flex flex-col items-center">
            <div 
              className={`w-10 h-10 rounded-full flex items-center justify-center ${currentStep >= step ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-600'}`}
            >
              {step}
            </div>
            <span className="text-xs mt-1 text-center">
              {step === 1 ? 'Assessment' : 
               step === 2 ? 'Profile' : 
               step === 3 ? 'Learning Plan' : 'Weekly Plan'}
            </span>
          </div>
        ))}
        <div className="absolute left-0 right-0 top-[4.5rem] px-6 z-0">
          <div className="h-1 bg-gray-200 relative">
            <div 
              className="h-1 bg-blue-600 absolute top-0 left-0 transition-all duration-500"
              style={{ width: `${(currentStep - 1) * 33.33}%` }}
            ></div>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="bg-gray-50 min-h-screen">
      {renderStepIndicator()}
      <div className="max-w-4xl mx-auto bg-white rounded-lg shadow-lg overflow-hidden relative">
        {renderStepContent()}
      </div>
      <div className="max-w-4xl mx-auto mt-4 flex justify-between px-4">
        <button
          onClick={onCancel}
          className="px-4 py-2 text-gray-600 hover:text-gray-800 transition-colors"
        >
          Cancel
        </button>
      </div>
    </div>
  );
};