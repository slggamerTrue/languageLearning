export interface Scene {
  description: string;
  current_situation: string;
  your_role: string;
  student_role: string;
  additional_info: string;
}

export interface KnowledgePoint {
  name: string;
}

export interface BaseLesson {
  mode: 'study' | 'practice';
  topic: string;
}

export interface StudyLesson extends BaseLesson {
  mode: 'study';
  knowledge_points: KnowledgePoint[];
}

export interface PracticeLesson extends BaseLesson {
  mode: 'practice';
  scene: Scene;
}

export type Lesson = StudyLesson | PracticeLesson;

export interface PracticeFormData {
  scene: Scene;
}
