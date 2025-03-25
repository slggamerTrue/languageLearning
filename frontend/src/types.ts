export interface Message {
    role: 'system' | 'user' | 'assistant';
    content: string;
    speechText?: string;
    displayText?: string | null;
}

export interface SceneResource {
    resource_type: 'menu' | 'document' | 'image' | 'list';
    title: string;
    content: string;
    display_format: 'markdown' | 'text' | 'table';
    speechText?: string;
}

export interface Scene {
    description: string;
    your_role: string;
    student_role: string;
    additional_info: string;
    current_situation: string;
    resources?: SceneResource[];
}

export interface KnowledgePoint {
    name: string;
    level: number;
    examples: string[];
    exercises: string[];
    scenario?: string;
}

export interface Material {
    type: string;
    title: string;
    segment: string;
    content: string;
}

export interface ReviewActivity {
    point: string;
    context: string;
    difficulty: number;
}

export interface BaseLesson {
    mode: 'study' | 'practice';
    topic: string;
    speechText: string;
    displayText: string;
}

export interface StudyLesson extends BaseLesson {
    mode: 'study';
    knowledge_points: KnowledgePoint[];
    day_number?: number;
    materials: Material[];
    review_activities: ReviewActivity[];
    estimated_time: number;
}

export interface PracticeLesson extends BaseLesson {
    mode: 'practice';
    scene: Scene;
}

export type Lesson = StudyLesson | PracticeLesson;

export interface WeeklyPlanDay {
    day_number: number;
    topic: string;
    materials: Material[];
    knowledge_points: KnowledgePoint[];
    review_activities: ReviewActivity[];
    estimated_time: number;
}
