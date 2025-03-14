import React, { useState, useEffect } from 'react';
import axios from 'axios';
import ReactMarkdown from 'react-markdown';
import './App.css';

// API base URL - use relative URL in production or absolute URL in development
const API_BASE_URL = process.env.NODE_ENV === 'production' 
  ? '/api' // In production, use relative path (served by same domain)
  : 'http://localhost:9000/api'; // In development, use explicit host
import { MessageDisplay } from './components/MessageDisplay';
import { ChatInput } from './components/ChatInput';
import { AssessmentFlow } from './components/AssessmentFlow';
import {
  Message,
  Scene,
  KnowledgePoint,
  Material,
  ReviewActivity,
  StudyLesson,
  PracticeLesson,
  Lesson,
  WeeklyPlanDay
} from './types';

interface BaseLesson {
  mode: 'study' | 'practice';
  topic: string;
  day_number?: number;
}

interface AssessmentDay {
  day_number: number;
  topic: string;
  materials: Material[];
  knowledge_points: KnowledgePoint[];
  review_activities: ReviewActivity[];
  estimated_time: number;
}

function App() {
  const [currentView, setCurrentView] = useState<'home' | 'courses' | 'assessment' | 'practice' | 'lesson'>('home');
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isWaitingResponse, setIsWaitingResponse] = useState(false);
  const [loadingStatus, setLoadingStatus] = useState('');
  const [lesson, setLesson] = useState<Lesson | null>(null);
  const [availableCourses, setAvailableCourses] = useState<Lesson[]>([]);
  
  const sampleCourses: Lesson[] = [
    {
      mode: 'study',
      topic: 'Greetings and Introductions in the Workplace',
      speech_text: 'Let me introduce you to basic workplace greetings and introductions...',
      display_text: '# Workplace Greetings and Introductions\n\n## Key Points:\n- Basic greetings\n- Self-introduction\n- Professional etiquette',
      knowledge_points: [
        {
          name: 'Basic Greetings',
          level: 1,
          examples: ['Good morning', 'Hello everyone'],
          exercises: ['Practice formal greetings']
        },
        {
          name: 'Self Introduction',
          level: 1,
          examples: ['My name is...', 'I work in...'],
          exercises: ['Introduce yourself to the team']
        }
      ],
      materials: [],
      review_activities: [],
      estimated_time: 30
    },
    {
      mode: 'practice',
      topic: 'Greetings and Introductions in the Workplace',
      speech_text: 'Now, let\'s practice introducing yourself in a professional setting...',
      display_text: '# Practice Scenario\n\nYou are a new employee attending your first team meeting.\n\n## Key Phrases:\n- "Hello everyone, I\'m [name]"\n- "I\'m excited to join the team"',
      scene: {
        description: 'First day at a new office',
        your_role: 'New employee',
        student_role: 'Team member',
        additional_info: 'This is your first team meeting',
        current_situation: 'You just entered the meeting room where your new team is waiting',
        resources: []
      }
    }
  ];

  const [practiceFormData, setPracticeFormData] = useState<PracticeLesson>({
    mode: 'practice',
    topic: '',
    speech_text: '',
    display_text: '',
    scene: {
      description: '',
      your_role: '',
      student_role: '',
      additional_info: '',
      current_situation: '',
      resources: []
    }
  });

  // Start the assessment flow using the new component
  const startInitialAssessment = () => {
    setCurrentView('assessment');
  };
  
  // Handle completion of the assessment flow
  const handleAssessmentComplete = (newLesson: any, conversationHistory: Message[]) => {
    setLesson(newLesson);
    setMessages(conversationHistory || []);
    setCurrentView('lesson');
  };
  
  // Handle cancellation of the assessment flow
  const handleAssessmentCancel = () => {
    setCurrentView('home');
  };

  const createCustomLesson = async (formData: PracticeLesson) => {
    try {
      setIsLoading(true);
      setLoadingStatus('正在创建课程...');
      const response = await axios.post(`${API_BASE_URL}/lesson/create`, formData);
      const { lesson: newLesson, conversation_history } = response.data;
      setLesson(newLesson);
      setMessages(conversation_history || []);
      setCurrentView('assessment');
    } catch (error) {
      console.error('Error creating lesson:', error);
    } finally {
      setIsLoading(false);
      setLoadingStatus('');
    }
  };

  const sendMessage = async () => {
    if (!input.trim()) return;
    
    // Check if we're not in assessment mode and there's no lesson
    if (currentView !== 'assessment' && !lesson) return;

    try {
      setIsLoading(true);
      const userMessage: Message = { role: 'user', content: input };
      
      // Add user message immediately
      const updatedMessages = [...messages, userMessage];
      setMessages(updatedMessages);
      setInput('');
      
      let response;
      
      if (currentView === 'assessment') {
        // Use assessment API endpoint
        response = await axios.post(
          `${API_BASE_URL}/assessment/initial-chat`,
          updatedMessages
        );
        
        // Handle assessment response
        const assistantMessage: Message = {
          role: 'assistant',
          content: response.data.content || response.data
        };
        setMessages([...updatedMessages, assistantMessage]);
        
        // Check if assessment is complete
        if (assistantMessage.content.includes('<ASSESSMENT_COMPLETE>')) {
          setLoadingStatus('正在分析对话内容...');
          
          // Analyze conversation to generate user profile
          const profileResponse = await axios.post(`${API_BASE_URL}/assessment/analyze-profile`, updatedMessages);
          const userProfile = profileResponse.data;
          
          setLoadingStatus('正在生成学习计划...');
          
          // Generate weekly plan using user profile
          const weeklyPlanResponse = await axios.post(`${API_BASE_URL}/assessment/generate-weekly-plan`, userProfile);
          const weeklyPlan = weeklyPlanResponse.data;
          
          // Create courses based on weekly plan - both study and practice modes for each topic
          const generatedCourses: Lesson[] = [];
          
          weeklyPlan.forEach((day: WeeklyPlanDay) => {
            // Create study mode lesson
            const studyLesson: StudyLesson = {
              mode: 'study',
              topic: day.topic,
              day_number: day.day_number,
              knowledge_points: day.knowledge_points,
              materials: day.materials,
              review_activities: day.review_activities,
              estimated_time: day.estimated_time,
              speech_text: `Welcome to Day ${day.day_number}: ${day.topic}`,
              display_text: `# Day ${day.day_number}: ${day.topic}\n\n## Knowledge Points:\n${day.knowledge_points.map((kp: any) => `- ${kp.name}`).join('\n')}`
            };
            
            // Create practice mode lesson with the same topic
            const practiceLesson: PracticeLesson = {
              mode: 'practice',
              topic: day.topic,
              speech_text: `Let's practice what we learned about ${day.topic}`,
              display_text: `# Practice: ${day.topic}\n\nLet's apply what we've learned in a real-world scenario.`,
              scene: {
                description: `Practice scenario for ${day.topic}`,
                your_role: 'English tutor',
                student_role: 'English learner',
                additional_info: `This practice session focuses on ${day.topic}`,
                current_situation: 'You are having a conversation to practice the learned concepts',
                resources: []
              }
            };
            
            // Add both lessons to the array
            generatedCourses.push(studyLesson, practiceLesson);
          });
          
          // Set available courses
          setAvailableCourses(generatedCourses);
          setIsLoading(false);
        }
      } else {
        // Use lesson API endpoint
        response = await axios.post(
          `${API_BASE_URL}/lesson/chat`,
          {
            lesson: lesson,
            conversation_history: updatedMessages,
            user_input: input
          }
        );
        
        // Update messages with the complete conversation history
        if (response.data.conversation_history) {
          setMessages(response.data.conversation_history);
        } else {
          // Fallback if conversation history is not provided
          const assistantMessage: Message = {
            role: 'assistant',
            content: response.data.content,
            speech_text: response.data.speech_text || response.data.content,
            display_text: response.data.display_text || response.data.content
          };
          setMessages([...updatedMessages, assistantMessage]);
        }
      }
    } catch (error) {
      console.error('Error sending message:', error);
      // Add error message
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: '抱歉，发生了一些错误，请稍后再试。',
        display_text: '# 出错了\n\n抱歉，在处理您的消息时遇到了问题。请稍后重试。',
        speech_text: '抱歉，发生了一些错误，请稍后再试。'
      }]);
    } finally {
      setIsLoading(false);
      setIsWaitingResponse(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-100 p-4">
      <div className="max-w-4xl mx-auto bg-white rounded-lg shadow-lg overflow-hidden">
        <div className="p-4 bg-blue-600 text-white">
          <h1 className="text-2xl font-bold">AI English Tutor</h1>
        </div>

        {currentView === 'home' ? (
          <div className="p-8 text-center">
            <h1 className="text-3xl font-bold mb-8">Welcome to AI English Tutor</h1>
            <div className="space-y-4">
              <button
                onClick={startInitialAssessment}
                className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 w-full max-w-md"
              >
                Start Assessment
              </button>
              <button
                onClick={() => setCurrentView('courses')}
                className="bg-green-600 text-white px-6 py-3 rounded-lg hover:bg-green-700 w-full max-w-md"
              >
                Browse Courses
              </button>
              <button
                onClick={() => setCurrentView('practice')}
                className="bg-purple-600 text-white px-6 py-3 rounded-lg hover:bg-purple-700 w-full max-w-md"
              >
                Custom Practice
              </button>
            </div>
          </div>
        ) : currentView === 'assessment' || currentView === 'lesson' ? (
          <div className="flex flex-col h-[600px] bg-gray-50">
            <div className="bg-white py-4 px-6 border-b flex items-center justify-between">
              <h2 className="text-xl font-semibold text-gray-800">AI English Tutor</h2>
              {isLoading && (
                <div className="flex items-center text-gray-600">
                  <div className="animate-spin mr-2 h-5 w-5 border-2 border-blue-500 border-t-transparent rounded-full"></div>
                  正在准备评估...
                </div>
              )}
            </div>
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
              {messages
                .filter(message => message.role !== 'system')
                .map((message, index) => (
                  <MessageDisplay key={index} message={message} />
                ))}
            </div>
            
            {availableCourses.length > 0 && (
              <div className="border-t p-4">
                <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-semibold">推荐课程</h3>
              <button
                className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 transition-colors"
                onClick={async () => {
                  setIsLoading(true);
                  setLoadingStatus('正在准备课程...');
                  try {
                    // 使用选定的课程数据
                    const selectedCourse = sampleCourses[0];
                    if (!selectedCourse) {
                      throw new Error('No course selected');
                    }
                    const studyCourse = selectedCourse as StudyLesson;
                    const sampleLesson: StudyLesson = {
                      mode: 'study',
                      topic: studyCourse.topic,
                      speech_text: `Let's start learning about ${studyCourse.topic}`,
                      display_text: `# ${studyCourse.topic}\n\n## Today's Learning Points`,
                      day_number: studyCourse.day_number,
                      materials: studyCourse.materials,
                      knowledge_points: studyCourse.knowledge_points,
                      review_activities: studyCourse.review_activities,
                      estimated_time: studyCourse.estimated_time
                    };
                    const response = await axios.post(`${API_BASE_URL}/lesson/create`, sampleLesson);
                    const { lesson: newLesson, conversation_history } = response.data;
                    setLesson(newLesson);
                    setMessages(conversation_history || []);
                  } catch (error) {
                    console.error('Error creating sample lesson:', error);
                  } finally {
                    setIsLoading(false);
                    setLoadingStatus('');
                  }
                }}
              >
                测试课程
              </button>
            </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {availableCourses.map((course, index) => (
                    <div key={index} className="border rounded-lg p-4 hover:shadow-lg transition-shadow cursor-pointer bg-white"
                         onClick={() => {
                           // Immediately switch to lesson view and show initial message
                           setCurrentView('lesson');
                           const initialMessages: Message[] = [
                             {
                               role: 'assistant' as const,
                               content: `欢迎来到《${course.topic}》课程！\n\n我正在为您准备课程内容，请稍候...`,
                               display_text: `# ${course.topic}\n\n正在为您准备以下内容：\n${course.mode === 'study' 
                                 ? `- ${(course as StudyLesson).knowledge_points.map(point => point.name).join('\n- ')}` 
                                 : `- ${(course as PracticeLesson).scene.description}`}\n\n请稍候...`
                             }
                           ];
                           setMessages(initialMessages);
                           
                           // Start lesson creation in background
                           (async () => {
                             try {
                               const request = course.mode === 'study' 
                                 ? { mode: 'study', topic: course.topic, assessment_day: course as StudyLesson } 
                                 : { mode: 'practice', topic: course.topic, scene: (course as PracticeLesson).scene };
                               const response = await axios.post(`${API_BASE_URL}/lesson/create`, request);
                               const { lesson: newLesson, conversation_history } = response.data;
                               setLesson(newLesson);
                               setMessages(conversation_history || []);
                             } catch (error) {
                               console.error('Error creating lesson:', error);
                               setMessages(prev => [...prev, {
                                 role: 'assistant' as const,
                                 content: '抱歉，加载课程时出现错误。请返回课程列表重试。',
                                 display_text: '# 出错了\n\n抱歉，在准备课程内容时遇到了问题。请点击返回按钮重试。'
                               }]);
                             }
                           })();
                         }}>
                      <div className={`text-xs font-semibold mb-2 inline-block px-2 py-1 rounded ${course.mode === 'study' ? 'bg-blue-100 text-blue-800' : 'bg-green-100 text-green-800'}`}>
                        {course.mode === 'study' ? '学习模式' : '练习模式'}
                      </div>
                      <h4 className="font-medium mb-2">{course.topic}</h4>
                      <p className="text-sm text-gray-600">
                        {course.mode === 'study' 
                          ? `知识点: ${(course as StudyLesson).knowledge_points.map(point => point.name).join(', ')}` 
                          : (course as PracticeLesson).scene.description}
                      </p>
                      <p className="text-sm text-gray-500 mt-2">
                        预计时间: {course.mode === 'study' 
                          ? `${(course as StudyLesson).estimated_time} minutes`
                          : (course as PracticeLesson).scene.current_situation.split('Estimated time:')[1]}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <ChatInput
              input={input}
              setInput={setInput}
              sendMessage={sendMessage}
              isLoading={isLoading}
            />
          </div>
        ) : currentView === 'practice' ? (
          <div className="p-8">
            <h3 className="text-xl mb-4 text-center">Customize Your Practice Session</h3>
            <form className="space-y-4" onSubmit={async (e) => {
              e.preventDefault();
              await createCustomLesson(practiceFormData);
            }}>
              <div>
                <label className="block text-sm font-medium mb-1">Topic</label>
                <input
                  type="text"
                  className="w-full p-2 border rounded"
                  value={practiceFormData.topic}
                  onChange={(e) => setPracticeFormData(prev => ({ ...prev, topic: e.target.value }))}
                  placeholder="例如：商务会议、日常对话等"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">场景描述</label>
                <textarea
                  className="w-full p-2 border rounded"
                  value={practiceFormData.scene.description}
                  onChange={(e) => setPracticeFormData(prev => ({ 
                    ...prev, 
                    scene: { ...prev.scene, description: e.target.value }
                  }))}
                  placeholder="描述练习场景的具体情况"
                  rows={3}
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">你的角色</label>
                <input
                  type="text"
                  className="w-full p-2 border rounded"
                  value={practiceFormData.scene.your_role}
                  onChange={(e) => setPracticeFormData(prev => ({ 
                    ...prev, 
                    scene: { ...prev.scene, your_role: e.target.value }
                  }))}
                  placeholder="例如：面试官、客户等"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">学生角色</label>
                <input
                  type="text"
                  className="w-full p-2 border rounded"
                  value={practiceFormData.scene.student_role}
                  onChange={(e) => setPracticeFormData(prev => ({ 
                    ...prev, 
                    scene: { ...prev.scene, student_role: e.target.value }
                  }))}
                  placeholder="例如：求职者、顾客等"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">补充信息</label>
                <textarea
                  className="w-full p-2 border rounded"
                  value={practiceFormData.scene.additional_info}
                  onChange={(e) => setPracticeFormData(prev => ({ 
                    ...prev, 
                    scene: { ...prev.scene, additional_info: e.target.value }
                  }))}
                  placeholder="任何需要补充的背景信息"
                  rows={2}
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">当前情况</label>
                <textarea
                  className="w-full p-2 border rounded"
                  value={practiceFormData.scene.current_situation}
                  onChange={(e) => setPracticeFormData(prev => ({ 
                    ...prev, 
                    scene: { ...prev.scene, current_situation: e.target.value }
                  }))}
                  placeholder="描述当前的具体情况"
                  rows={2}
                  required
                />
              </div>
              <div className="flex justify-end space-x-4">
                <button
                  type="button"
                  onClick={() => setCurrentView('home')}
                  className="bg-gray-300 text-gray-700 px-4 py-2 rounded-lg hover:bg-gray-400"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700"
                  disabled={isLoading}
                >
                  {isLoading ? 'Creating...' : 'Start Practice'}
                </button>
              </div>
            </form>
          </div>
        ) : currentView === 'courses' ? (
          <div className="p-8">
            <h3 className="text-xl mb-4 text-center">Available Courses</h3>
            <div className="grid gap-4 md:grid-cols-2">
              {sampleCourses.map((course, index) => (
                <div key={index} className="border rounded-lg p-4 hover:shadow-lg transition-shadow cursor-pointer bg-white"
                     onClick={async () => {
                       setIsLoading(true);
                       setLoadingStatus('正在创建课程...');
                       try {
                         const request = course.mode === 'study' 
                           ? { mode: 'study', topic: course.topic, assessment_day: course as StudyLesson } 
                           : { mode: 'practice', topic: course.topic, scene: (course as PracticeLesson).scene };
                         const response = await axios.post('http://localhost:9000/api/lesson/create', request);
                         const { lesson: newLesson, conversation_history } = response.data;
                         setLesson(newLesson);
                         setMessages(conversation_history || []);
                         setCurrentView('lesson');
                       } catch (error) {
                         console.error('Error creating lesson:', error);
                       } finally {
                         setIsLoading(false);
                         setLoadingStatus('');
                       }
                     }}>
                  <div className={`text-xs font-semibold mb-2 inline-block px-2 py-1 rounded ${course.mode === 'study' ? 'bg-blue-100 text-blue-800' : 'bg-green-100 text-green-800'}`}>
                    {course.mode === 'study' ? '学习模式' : '练习模式'}
                  </div>
                  <h4 className="font-medium mb-2">{course.topic}</h4>
                  <p className="text-sm text-gray-600">
                    {(() => {
                      if (course.mode === 'study') {
                        const studyCourse = course as StudyLesson;
                        return `知识点: ${studyCourse.knowledge_points.map(point => point.name).join(', ')}`;
                      } else {
                        const practiceCourse = course as PracticeLesson;
                        return practiceCourse.scene.description;
                      }
                    })()}
                  </p>
                  <p className="text-sm text-gray-500 mt-2">
                    预计时间: {course.mode === 'study' 
                      ? `${(course as StudyLesson).estimated_time} minutes`
                      : '30 minutes'}
                  </p>
                </div>
              ))}
            </div>
          </div>
        ) : (
          <div className="flex flex-col h-[600px]">
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
              {messages
                .filter(message => message.role !== 'system')
                .map((message, index) => (
                  <div
                    key={index}
                    className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                  >
                    <div
                      className={`max-w-[80%] rounded-lg p-3 ${message.role === 'user' 
                        ? 'bg-blue-100' 
                        : message.content === '...' 
                          ? 'bg-gray-100 animate-pulse' 
                          : 'bg-gray-100'}`}
                    >
                      {message.role === 'assistant' && message.display_text && (
                        <div className="markdown-content prose dark:prose-invert max-w-none mb-2">
                          <ReactMarkdown>{message.display_text}</ReactMarkdown>
                        </div>
                      )}
                      <div className="whitespace-pre-wrap">
                        {message.role === 'assistant' ? (message.speech_text || message.content) : message.content}
                      </div>
                    </div>
                  </div>
              ))}
            </div>

            <div className="p-4 border-t">
              <div className="flex space-x-2">
                <input
                  type="text"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
                  placeholder="Type your message..."
                  className="flex-1 border rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  disabled={isLoading}
                />
                <button
                  onClick={sendMessage}
                  disabled={isLoading}
                  className="bg-blue-600 text-white px-6 py-2 rounded-lg font-semibold hover:bg-blue-700 disabled:opacity-50"
                >
                  {isLoading ? 'Sending...' : 'Send'}
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
