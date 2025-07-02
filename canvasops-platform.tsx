import React, { useState } from 'react';
import { Play, Upload, Shield, CheckCircle, XCircle, Clock, ExternalLink, AlertTriangle, Download, Eye, Settings } from 'lucide-react';

const CanvasOps = () => {
  const [currentView, setCurrentView] = useState('landing');
  const [selectedTool, setSelectedTool] = useState(null);
  const [executionMode, setExecutionMode] = useState('preview');
  const [executionResults, setExecutionResults] = useState(null);
  const [submissionData, setSubmissionData] = useState({
    name: '',
    description: '',
    whenToUse: '',
    inputs: [{ name: '', type: 'text', description: '', required: true }],
    tags: [],
    isDestructive: false
  });

  // Sample tools data
  const tools = [
    {
      id: 'link-checker',
      name: 'Link Checker',
      description: 'Scan course content for broken or invalid links',
      tags: ['QA', 'Links'],
      isDestructive: false,
      inputs: [
        { name: 'checkExternal', type: 'boolean', description: 'Check external links (slower)', required: false },
        { name: 'includeFiles', type: 'boolean', description: 'Include file attachments', required: false }
      ],
      scope: 'Pages, Modules, Assignments, Announcements'
    },
    {
      id: 'find-replace',
      name: 'Find & Replace URLs',
      description: 'Search for specific URLs in course content and replace them with new ones',
      tags: ['QA', 'URLs', 'Content'],
      isDestructive: true,
      inputs: [
        { name: 'includeContent', type: 'multiselect', options: ['syllabus', 'pages', 'assignments', 'quizzes', 'discussions', 'announcements', 'modules'], description: 'Content types to scan', required: true }
      ],
      scope: 'Course content, modules, assignments, pages, quizzes, discussions',
      supportsSubaccount: true
    },
    {
      id: 'due-date-audit',
      name: 'Due Date Audit',
      description: 'List and optionally fix assignment and quiz due dates',
      tags: ['Dates'],
      isDestructive: false,
      inputs: [
        { name: 'termStartDate', type: 'date', description: 'Term start date', required: true },
        { name: 'termEndDate', type: 'date', description: 'Term end date', required: true }
      ],
      scope: 'Assignments, Quizzes, Discussions'
    },
    {
      id: 'navigation-cleaner',
      name: 'Navigation Cleaner',
      description: 'Check and clean up course navigation menu items',
      tags: ['UX', 'Menus'],
      isDestructive: false,
      inputs: [
        { name: 'hideUnpublished', type: 'boolean', description: 'Hide unpublished items', required: false }
      ],
      scope: 'Course Navigation'
    },
    {
      id: 'orphaned-pages',
      name: 'Orphaned Pages Finder',
      description: 'Find pages not linked in any module or navigation',
      tags: ['Pages'],
      isDestructive: false,
      inputs: [],
      scope: 'Course Pages and Modules'
    }
  ];

  const pendingScripts = [
    {
      id: 1,
      name: 'Grade Export Formatter',
      submitter: 'Sarah Johnson',
      submittedDate: '2025-06-28',
      tags: ['Grades', 'Export'],
      isDestructive: false,
      aiValidation: 'passed',
      description: 'Formats exported grades for institutional reporting'
    },
    {
      id: 2,
      name: 'Bulk File Organizer',
      submitter: 'Mike Chen',
      submittedDate: '2025-06-27',
      tags: ['Files'],
      isDestructive: true,
      aiValidation: 'warning',
      description: 'Organizes course files into folders by content type'
    }
  ];

  const LandingPage = () => (
    <div className="min-h-screen bg-gradient-to-br from-stone-100 to-stone-200 flex items-center justify-center p-4">
      <div className="max-w-4xl w-full">
        <div className="text-center mb-12">
          <h1 className="text-5xl font-bold text-gray-900 mb-4">CanvasOps</h1>
          <p className="text-xl text-stone-700 mb-2">Canvas Automation Platform for ACU</p>
          <p className="text-stone-600">Streamline your Canvas course management with automated tools</p>
        </div>
        
        <div className="grid md:grid-cols-3 gap-8">
          <div 
            onClick={() => setCurrentView('runner')}
            className="bg-white rounded-xl shadow-lg p-8 cursor-pointer hover:shadow-xl transition-shadow group"
          >
            <div className="text-center">
              <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4 group-hover:bg-red-200 transition-colors">
                <Play className="w-8 h-8 text-red-600" />
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">Run a Tool</h3>
              <p className="text-stone-600 mb-4">Execute automation scripts on your Canvas courses</p>
              <div className="text-sm text-stone-500">
                <div>• Link checking</div>
                <div>• Content updates</div>
                <div>• QA automation</div>
              </div>
            </div>
          </div>

          <div 
            onClick={() => setCurrentView('submitter')}
            className="bg-white rounded-xl shadow-lg p-8 cursor-pointer hover:shadow-xl transition-shadow group"
          >
            <div className="text-center">
              <div className="w-16 h-16 bg-purple-100 rounded-full flex items-center justify-center mx-auto mb-4 group-hover:bg-purple-200 transition-colors">
                <Upload className="w-8 h-8 text-purple-700" />
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">Submit a Script</h3>
              <p className="text-stone-600 mb-4">Contribute new automation tools to the platform</p>
              <div className="text-sm text-stone-500">
                <div>• Share your scripts</div>
                <div>• AI validation</div>
                <div>• Peer review</div>
              </div>
            </div>
          </div>

          <div 
            onClick={() => setCurrentView('admin')}
            className="bg-white rounded-xl shadow-lg p-8 cursor-pointer hover:shadow-xl transition-shadow group"
          >
            <div className="text-center">
              <div className="w-16 h-16 bg-stone-300 rounded-full flex items-center justify-center mx-auto mb-4 group-hover:bg-stone-400 transition-colors">
                <Shield className="w-8 h-8 text-stone-700" />
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">Admin Review</h3>
              <p className="text-stone-600 mb-4">Review and approve submitted scripts</p>
              <div className="text-sm text-stone-500">
                <div>• Script validation</div>
                <div>• Security review</div>
                <div>• Approval workflow</div>
              </div>
            </div>
          </div>
        </div>

        <div className="mt-12 text-center">
          <p className="text-sm text-stone-500">
            Secure • Sandboxed • API Token stays in memory only
          </p>
        </div>
      </div>
    </div>
  );

  const ToolRunner = () => (
    <div className="min-h-screen bg-stone-50">
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-6xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <button 
              onClick={() => setCurrentView('landing')}
              className="text-red-600 hover:text-red-800 font-medium"
            >
              ← Back to Home
            </button>
            <h1 className="text-2xl font-bold text-gray-900">Tool Runner</h1>
          </div>
          <div className="text-sm text-stone-500">
            Learning Technologist Tools
          </div>
        </div>
      </div>

      {!selectedTool ? (
        <div className="max-w-6xl mx-auto p-6">
          <div className="mb-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-2">Available Tools</h2>
            <p className="text-stone-600">Select a tool to run on your Canvas course</p>
          </div>
          
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {tools.map(tool => (
              <div 
                key={tool.id}
                onClick={() => setSelectedTool(tool)}
                className="bg-white rounded-lg shadow border border-gray-200 p-6 cursor-pointer hover:shadow-md transition-shadow"
              >
                <div className="flex items-start justify-between mb-3">
                  <h3 className="font-semibold text-gray-900">{tool.name}</h3>
                  {tool.isDestructive && (
                    <AlertTriangle className="w-5 h-5 text-orange-500 flex-shrink-0" />
                  )}
                </div>
                <p className="text-stone-600 text-sm mb-3">{tool.description}</p>
                <div className="flex flex-wrap gap-1 mb-3">
                  {tool.tags.map(tag => (
                    <span key={tag} className="px-2 py-1 bg-purple-100 text-purple-700 text-xs rounded">
                      {tag}
                    </span>
                  ))}
                </div>
                <div className="text-xs text-stone-500">
                  Scope: {tool.scope}
                </div>
              </div>
            ))}
          </div>
        </div>
      ) : (
        <ToolExecutor tool={selectedTool} />
      )}
    </div>
  );

  const ToolExecutor = ({ tool }) => {
    const [formData, setFormData] = useState({
      canvasUrl: '',
      apiToken: '',
      processingMode: 'course', // 'course' or 'subaccount'
      targetId: '', // courseId or subaccountId
      inputs: {},
      urlMappings: [{ oldUrl: '', newUrl: '' }] // For find-replace tool
    });

    const handleInputChange = (field, value) => {
      if (field.startsWith('input_')) {
        const inputName = field.replace('input_', '');
        setFormData(prev => ({
          ...prev,
          inputs: { ...prev.inputs, [inputName]: value }
        }));
      } else {
        setFormData(prev => ({ ...prev, [field]: value }));
      }
    };

    const executeScript = async () => {
      if (tool.id === 'find-replace') {
        await executeFindReplaceScript();
      } else {
        // Simulate other scripts
        const mockResults = {
          'link-checker': {
            summary: 'Found 3 broken links out of 47 total links checked',
            details: [
              { type: 'broken', url: 'https://oldsite.example.com/resource', location: 'Module 2 - Week 3 Page' },
              { type: 'broken', url: 'https://expired.edu/document.pdf', location: 'Assignment Instructions' },
              { type: 'broken', url: 'https://deadlink.com/image.jpg', location: 'Course Introduction Page' }
            ],
            totalChecked: 47,
            brokenCount: 3
          }
        };
        setExecutionResults(mockResults[tool.id] || { summary: 'Tool executed successfully', details: [] });
      }
    };

    const executeFindReplaceScript = async () => {
      try {
        setExecutionResults({ summary: 'Processing...', details: [] });
        
        const findings = [];
        const canvasApi = new CanvasAPI(formData.canvasUrl, formData.apiToken);
        
        // Create URL mappings object
        const urlMappings = {};
        formData.urlMappings.forEach(mapping => {
          if (mapping.oldUrl && mapping.newUrl) {
            urlMappings[mapping.oldUrl] = mapping.newUrl;
          }
        });

        if (Object.keys(urlMappings).length === 0) {
          setExecutionResults({ 
            summary: 'Error: No valid URL mappings provided', 
            details: [],
            error: true 
          });
          return;
        }

        let coursesToProcess = [];
        
        if (formData.processingMode === 'course') {
          coursesToProcess = [{ id: formData.targetId, name: 'Target Course' }];
        } else {
          // Get courses from subaccount
          const courses = await canvasApi.getCoursesInSubaccount(
            formData.targetId,
            formData.inputs.termFilter,
            formData.inputs.workflowState
          );
          coursesToProcess = courses;
        }

        let totalReplacements = 0;
        const contentTypes = formData.inputs.includeContent || [];

        for (const course of coursesToProcess) {
          const courseFindings = await canvasApi.scanAndReplaceInCourse(
            course.id,
            urlMappings,
            contentTypes,
            executionMode === 'preview'
          );
          findings.push(...courseFindings);
          totalReplacements += courseFindings.length;
        }

        setExecutionResults({
          summary: `${executionMode === 'preview' ? 'Preview: Would replace' : 'Replaced'} ${totalReplacements} URLs across ${coursesToProcess.length} course(s)`,
          details: findings.slice(0, 10), // Show first 10 for UI
          totalReplacements,
          coursesProcessed: coursesToProcess.length,
          allFindings: findings,
          reportGenerated: true
        });

      } catch (error) {
        setExecutionResults({
          summary: `Error: ${error.message}`,
          details: [],
          error: true
        });
      }
    };

    // Canvas API Class
    class CanvasAPI {
      constructor(baseUrl, apiToken) {
        this.baseUrl = baseUrl.replace(/\/$/, '');
        this.apiUrl = `${this.baseUrl}/api/v1`;
        this.headers = {
          'Authorization': `Bearer ${apiToken}`,
          'Content-Type': 'application/json'
        };
      }

      async makeRequest(endpoint, options = {}) {
        const url = `${this.apiUrl}/${endpoint}`;
        const response = await fetch(url, {
          ...options,
          headers: this.headers
        });
        
        if (!response.ok) {
          throw new Error(`Canvas API Error: ${response.status} ${response.statusText}`);
        }
        
        return response.json();
      }

      async getCoursesInSubaccount(subaccountId, termFilter, workflowState) {
        let endpoint = `accounts/${subaccountId}/courses?per_page=100`;
        
        if (termFilter) {
          endpoint += `&enrollment_term_id=${termFilter}`;
        }
        
        if (workflowState && workflowState !== 'all') {
          endpoint += `&state[]=${workflowState}`;
        }

        return this.makeRequest(endpoint);
      }

      async scanAndReplaceInCourse(courseId, urlMappings, contentTypes, isPreview) {
        const findings = [];
        
        try {
          // Get course info
          const course = await this.makeRequest(`courses/${courseId}`);
          
          // Process each content type
          for (const contentType of contentTypes) {
            switch (contentType) {
              case 'syllabus':
                const syllabusFindings = await this.processSyllabus(courseId, course.name, urlMappings, isPreview);
                findings.push(...syllabusFindings);
                break;
              case 'pages':
                const pageFindings = await this.processPages(courseId, course.name, urlMappings, isPreview);
                findings.push(...pageFindings);
                break;
              case 'assignments':
                const assignmentFindings = await this.processAssignments(courseId, course.name, urlMappings, isPreview);
                findings.push(...assignmentFindings);
                break;
              case 'quizzes':
                const quizFindings = await this.processQuizzes(courseId, course.name, urlMappings, isPreview);
                findings.push(...quizFindings);
                break;
              case 'discussions':
                const discussionFindings = await this.processDiscussions(courseId, course.name, urlMappings, isPreview);
                findings.push(...discussionFindings);
                break;
              case 'announcements':
                const announcementFindings = await this.processAnnouncements(courseId, course.name, urlMappings, isPreview);
                findings.push(...announcementFindings);
                break;
            }
          }
        } catch (error) {
          console.error(`Error processing course ${courseId}:`, error);
        }

        return findings;
      }

      replaceUrlsInContent(content, urlMappings) {
        if (!content) return { newContent: content, replacements: [] };
        
        let newContent = content;
        const replacements = [];
        
        for (const [oldUrl, newUrl] of Object.entries(urlMappings)) {
          if (newContent.includes(oldUrl)) {
            newContent = newContent.replaceAll(oldUrl, newUrl);
            replacements.push({ oldUrl, newUrl });
          }
        }
        
        return { newContent, replacements };
      }

      async processSyllabus(courseId, courseName, urlMappings, isPreview) {
        try {
          const course = await this.makeRequest(`courses/${courseId}?include[]=syllabus_body`);
          
          if (course.syllabus_body) {
            const { newContent, replacements } = this.replaceUrlsInContent(course.syllabus_body, urlMappings);
            
            if (replacements.length > 0 && !isPreview) {
              await this.makeRequest(`courses/${courseId}`, {
                method: 'PUT',
                body: JSON.stringify({
                  course: { syllabus_body: newContent }
                })
              });
            }
            
            return replacements.map(r => ({
              courseId,
              courseName,
              contentType: 'Syllabus',
              location: `${this.baseUrl}/courses/${courseId}/assignments/syllabus`,
              oldUrl: r.oldUrl,
              newUrl: r.newUrl,
              status: isPreview ? 'Preview' : 'Updated'
            }));
          }
        } catch (error) {
          console.error('Error processing syllabus:', error);
        }
        return [];
      }

      async processPages(courseId, courseName, urlMappings, isPreview) {
        const findings = [];
        try {
          const pages = await this.makeRequest(`courses/${courseId}/pages`);
          
          for (const page of pages) {
            const pageDetail = await this.makeRequest(`courses/${courseId}/pages/${page.url}`);
            
            if (pageDetail.body) {
              const { newContent, replacements } = this.replaceUrlsInContent(pageDetail.body, urlMappings);
              
              if (replacements.length > 0 && !isPreview) {
                await this.makeRequest(`courses/${courseId}/pages/${page.url}`, {
                  method: 'PUT',
                  body: JSON.stringify({
                    wiki_page: { body: newContent }
                  })
                });
              }
              
              findings.push(...replacements.map(r => ({
                courseId,
                courseName,
                contentType: 'Page',
                location: pageDetail.html_url,
                oldUrl: r.oldUrl,
                newUrl: r.newUrl,
                status: isPreview ? 'Preview' : 'Updated'
              })));
            }
          }
        } catch (error) {
          console.error('Error processing pages:', error);
        }
        return findings;
      }

      async processAssignments(courseId, courseName, urlMappings, isPreview) {
        const findings = [];
        try {
          const assignments = await this.makeRequest(`courses/${courseId}/assignments`);
          
          for (const assignment of assignments) {
            if (assignment.description) {
              const { newContent, replacements } = this.replaceUrlsInContent(assignment.description, urlMappings);
              
              if (replacements.length > 0 && !isPreview) {
                await this.makeRequest(`courses/${courseId}/assignments/${assignment.id}`, {
                  method: 'PUT',
                  body: JSON.stringify({
                    assignment: { description: newContent }
                  })
                });
              }
              
              findings.push(...replacements.map(r => ({
                courseId,
                courseName,
                contentType: 'Assignment',
                location: assignment.html_url,
                oldUrl: r.oldUrl,
                newUrl: r.newUrl,
                status: isPreview ? 'Preview' : 'Updated'
              })));
            }
          }
        } catch (error) {
          console.error('Error processing assignments:', error);
        }
        return findings;
      }

      async processQuizzes(courseId, courseName, urlMappings, isPreview) {
        const findings = [];
        try {
          const quizzes = await this.makeRequest(`courses/${courseId}/quizzes`);
          
          for (const quiz of quizzes) {
            if (quiz.description) {
              const { newContent, replacements } = this.replaceUrlsInContent(quiz.description, urlMappings);
              
              if (replacements.length > 0 && !isPreview) {
                await this.makeRequest(`courses/${courseId}/quizzes/${quiz.id}`, {
                  method: 'PUT',
                  body: JSON.stringify({
                    quiz: { description: newContent }
                  })
                });
              }
              
              findings.push(...replacements.map(r => ({
                courseId,
                courseName,
                contentType: 'Quiz',
                location: quiz.html_url,
                oldUrl: r.oldUrl,
                newUrl: r.newUrl,
                status: isPreview ? 'Preview' : 'Updated'
              })));
            }
          }
        } catch (error) {
          console.error('Error processing quizzes:', error);
        }
        return findings;
      }

      async processDiscussions(courseId, courseName, urlMappings, isPreview) {
        const findings = [];
        try {
          const discussions = await this.makeRequest(`courses/${courseId}/discussion_topics`);
          
          for (const discussion of discussions) {
            if (discussion.message) {
              const { newContent, replacements } = this.replaceUrlsInContent(discussion.message, urlMappings);
              
              if (replacements.length > 0 && !isPreview) {
                await this.makeRequest(`courses/${courseId}/discussion_topics/${discussion.id}`, {
                  method: 'PUT',
                  body: JSON.stringify({
                    message: newContent
                  })
                });
              }
              
              findings.push(...replacements.map(r => ({
                courseId,
                courseName,
                contentType: 'Discussion',
                location: discussion.html_url,
                oldUrl: r.oldUrl,
                newUrl: r.newUrl,
                status: isPreview ? 'Preview' : 'Updated'
              })));
            }
          }
        } catch (error) {
          console.error('Error processing discussions:', error);
        }
        return findings;
      }

      async processAnnouncements(courseId, courseName, urlMappings, isPreview) {
        const findings = [];
        try {
          const announcements = await this.makeRequest(`courses/${courseId}/discussion_topics?only_announcements=true`);
          
          for (const announcement of announcements) {
            if (announcement.message) {
              const { newContent, replacements } = this.replaceUrlsInContent(announcement.message, urlMappings);
              
              if (replacements.length > 0 && !isPreview) {
                await this.makeRequest(`courses/${courseId}/discussion_topics/${announcement.id}`, {
                  method: 'PUT',
                  body: JSON.stringify({
                    message: newContent
                  })
                });
              }
              
              findings.push(...replacements.map(r => ({
                courseId,
                courseName,
                contentType: 'Announcement',
                location: announcement.html_url,
                oldUrl: r.oldUrl,
                newUrl: r.newUrl,
                status: isPreview ? 'Preview' : 'Updated'
              })));
            }
          }
        } catch (error) {
          console.error('Error processing announcements:', error);
        }
        return findings;
      }
    }

    return (
      <div className="max-w-4xl mx-auto p-6">
        <div className="bg-white rounded-lg shadow border border-gray-200 p-6 mb-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-3">
              <button 
                onClick={() => setSelectedTool(null)}
                className="text-blue-600 hover:text-blue-800"
              >
                ← Back to Tools
              </button>
              <h2 className="text-xl font-semibold text-gray-900">{tool.name}</h2>
              {tool.isDestructive && (
                <span className="px-2 py-1 bg-orange-100 text-orange-700 text-xs rounded font-medium">
                  DESTRUCTIVE
                </span>
              )}
            </div>
          </div>
          
          <p className="text-gray-600 mb-4">{tool.description}</p>
          
          <div className="bg-purple-50 border border-purple-200 rounded p-3 mb-6">
            <p className="text-sm text-purple-800">
              <strong>Scope:</strong> {tool.scope}
            </p>
          </div>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Canvas URL *
              </label>
              <input
                type="url"
                value={formData.canvasUrl}
                onChange={(e) => handleInputChange('canvasUrl', e.target.value)}
                placeholder="https://acu.instructure.com"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-red-500 focus:border-red-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                API Token *
              </label>
              <input
                type="password"
                value={formData.apiToken}
                onChange={(e) => handleInputChange('apiToken', e.target.value)}
                placeholder="Your Canvas API token"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-red-500 focus:border-red-500"
              />
              <p className="text-xs text-gray-500 mt-1">Token is stored in memory only and never saved</p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {formData.processingMode === 'course' ? 'Course ID' : 'Subaccount ID'} *
              </label>
              <input
                type="text"
                value={formData.targetId}
                onChange={(e) => handleInputChange('targetId', e.target.value)}
                placeholder={formData.processingMode === 'course' ? "12345" : "67890"}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-red-500 focus:border-red-500"
              />
            </div>

            {tool.supportsSubaccount && (
              <div className="border-t pt-4">
                <h3 className="font-medium text-gray-900 mb-3">Processing Scope</h3>
                <div className="space-y-2">
                  <label className="flex items-center">
                    <input
                      type="radio"
                      value="course"
                      checked={formData.processingMode === 'course'}
                      onChange={(e) => setFormData(prev => ({ ...prev, processingMode: e.target.value }))}
                      className="text-red-600 focus:ring-red-500"
                    />
                    <span className="ml-2 text-sm">
                      <strong>Single Course</strong> - Process one specific course
                    </span>
                  </label>
                  <label className="flex items-center">
                    <input
                      type="radio"
                      value="subaccount"
                      checked={formData.processingMode === 'subaccount'}
                      onChange={(e) => setFormData(prev => ({ ...prev, processingMode: e.target.value }))}
                      className="text-red-600 focus:ring-red-500"
                    />
                    <span className="ml-2 text-sm">
                      <strong>Entire Subaccount</strong> - Process all courses in a subaccount
                    </span>
                  </label>
                </div>
              </div>
            )}

            {formData.processingMode === 'subaccount' && tool.supportsSubaccount && (
              <div className="border-t pt-4">
                <h3 className="font-medium text-gray-900 mb-3">Subaccount Filters</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Term Filter (optional)
                    </label>
                    <input
                      type="text"
                      value={formData.inputs.termFilter || ''}
                      onChange={(e) => handleInputChange('input_termFilter', e.target.value)}
                      placeholder="Term ID"
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-red-500 focus:border-red-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Course State
                    </label>
                    <select
                      value={formData.inputs.workflowState || 'all'}
                      onChange={(e) => handleInputChange('input_workflowState', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-red-500 focus:border-red-500"
                    >
                      <option value="all">All courses</option>
                      <option value="published">Published only</option>
                      <option value="unpublished">Unpublished only</option>
                    </select>
                  </div>
                </div>
              </div>
            )}

            {tool.id === 'find-replace' && (
              <div className="border-t pt-4">
                <h3 className="font-medium text-gray-900 mb-3">URL Mappings</h3>
                <div className="space-y-3">
                  {formData.urlMappings.map((mapping, index) => (
                    <div key={index} className="grid grid-cols-1 md:grid-cols-2 gap-3 p-3 border border-gray-200 rounded">
                      <div>
                        <label className="block text-xs font-medium text-gray-700 mb-1">Old URL</label>
                        <input
                          type="url"
                          value={mapping.oldUrl}
                          onChange={(e) => {
                            const newMappings = [...formData.urlMappings];
                            newMappings[index].oldUrl = e.target.value;
                            setFormData(prev => ({ ...prev, urlMappings: newMappings }));
                          }}
                          placeholder="https://old-domain.com/resource"
                          className="w-full px-2 py-1 border border-gray-300 rounded text-sm focus:ring-red-500 focus:border-red-500"
                        />
                      </div>
                      <div className="flex gap-2">
                        <div className="flex-1">
                          <label className="block text-xs font-medium text-gray-700 mb-1">New URL</label>
                          <input
                            type="url"
                            value={mapping.newUrl}
                            onChange={(e) => {
                              const newMappings = [...formData.urlMappings];
                              newMappings[index].newUrl = e.target.value;
                              setFormData(prev => ({ ...prev, urlMappings: newMappings }));
                            }}
                            placeholder="https://new-domain.com/resource"
                            className="w-full px-2 py-1 border border-gray-300 rounded text-sm focus:ring-red-500 focus:border-red-500"
                          />
                        </div>
                        {formData.urlMappings.length > 1 && (
                          <button
                            onClick={() => {
                              const newMappings = formData.urlMappings.filter((_, i) => i !== index);
                              setFormData(prev => ({ ...prev, urlMappings: newMappings }));
                            }}
                            className="mt-5 px-2 py-1 text-red-600 hover:text-red-800 text-sm"
                          >
                            Remove
                          </button>
                        )}
                      </div>
                    </div>
                  ))}
                  <button
                    onClick={() => {
                      setFormData(prev => ({
                        ...prev,
                        urlMappings: [...prev.urlMappings, { oldUrl: '', newUrl: '' }]
                      }));
                    }}
                    className="text-red-600 hover:text-red-800 text-sm font-medium"
                  >
                    + Add URL Mapping
                  </button>
                </div>
              </div>
            )}

            {tool.inputs.length > 0 && (
              <div className="border-t pt-4">
                <h3 className="font-medium text-gray-900 mb-3">Tool Settings</h3>
                {tool.inputs.map(input => (
                  <div key={input.name} className="mb-3">
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      {input.name.charAt(0).toUpperCase() + input.name.slice(1).replace(/([A-Z])/g, ' $1')}
                      {input.required && ' *'}
                    </label>
                    {input.type === 'boolean' ? (
                      <label className="flex items-center">
                        <input
                          type="checkbox"
                          checked={formData.inputs[input.name] || false}
                          onChange={(e) => handleInputChange(`input_${input.name}`, e.target.checked)}
                          className="rounded border-gray-300 text-red-600 focus:ring-red-500"
                        />
                        <span className="ml-2 text-sm text-gray-600">{input.description}</span>
                      </label>
                    ) : input.type === 'textarea' ? (
                      <>
                        <textarea
                          value={formData.inputs[input.name] || ''}
                          onChange={(e) => handleInputChange(`input_${input.name}`, e.target.value)}
                          placeholder={input.description}
                          rows={4}
                          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-red-500 focus:border-red-500"
                        />
                        <p className="text-xs text-gray-500 mt-1">{input.description}</p>
                      </>
                    ) : input.type === 'select' ? (
                      <>
                        <select
                          value={formData.inputs[input.name] || ''}
                          onChange={(e) => handleInputChange(`input_${input.name}`, e.target.value)}
                          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-red-500 focus:border-red-500"
                        >
                          <option value="">Select option...</option>
                          {input.options?.map(option => (
                            <option key={option} value={option}>{option}</option>
                          ))}
                        </select>
                        <p className="text-xs text-gray-500 mt-1">{input.description}</p>
                      </>
                    ) : input.type === 'multiselect' ? (
                      <>
                        <div className="space-y-2">
                          {input.options?.map(option => (
                            <label key={option} className="flex items-center">
                              <input
                                type="checkbox"
                                checked={(formData.inputs[input.name] || []).includes(option)}
                                onChange={(e) => {
                                  const currentValues = formData.inputs[input.name] || [];
                                  const newValues = e.target.checked 
                                    ? [...currentValues, option]
                                    : currentValues.filter(v => v !== option);
                                  handleInputChange(`input_${input.name}`, newValues);
                                }}
                                className="rounded border-gray-300 text-red-600 focus:ring-red-500"
                              />
                              <span className="ml-2 text-sm">{option}</span>
                            </label>
                          ))}
                        </div>
                        <p className="text-xs text-gray-500 mt-1">{input.description}</p>
                      </>
                    ) : (
                      <>
                        <input
                          type={input.type}
                          value={formData.inputs[input.name] || ''}
                          onChange={(e) => handleInputChange(`input_${input.name}`, e.target.value)}
                          placeholder={input.description}
                          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-red-500 focus:border-red-500"
                        />
                        <p className="text-xs text-gray-500 mt-1">{input.description}</p>
                      </>
                    )}
                  </div>
                ))}
              </div>
            )}

            <div className="border-t pt-4">
              <h3 className="font-medium text-gray-900 mb-3">Execution Mode</h3>
              <div className="space-y-2">
                <label className="flex items-center">
                  <input
                    type="radio"
                    value="preview"
                    checked={executionMode === 'preview'}
                    onChange={(e) => setExecutionMode(e.target.value)}
                    className="text-red-600 focus:ring-red-500"
                  />
                  <span className="ml-2 text-sm">
                    <strong>Preview (Dry Run)</strong> - See what would be changed without making modifications
                  </span>
                </label>
                <label className="flex items-center">
                  <input
                    type="radio"
                    value="live"
                    checked={executionMode === 'live'}
                    onChange={(e) => setExecutionMode(e.target.value)}
                    className="text-red-600 focus:ring-red-500"
                  />
                  <span className="ml-2 text-sm">
                    <strong>Live Run</strong> - Execute changes on the course
                    {tool.isDestructive && <span className="text-orange-600 font-medium"> (DESTRUCTIVE)</span>}
                  </span>
                </label>
              </div>
            </div>

            {tool.isDestructive && executionMode === 'live' && (
              <div className="bg-orange-50 border border-orange-200 rounded p-3">
                <div className="flex items-center space-x-2">
                  <AlertTriangle className="w-5 h-5 text-orange-600" />
                  <p className="text-sm text-orange-800 font-medium">
                    Warning: This tool will modify your course content. Please ensure you have a backup.
                  </p>
                </div>
              </div>
            )}

            <div className="flex space-x-3 pt-4">
              <button
                onClick={executeScript}
                disabled={!formData.canvasUrl || !formData.apiToken || !formData.targetId}
                className="flex items-center space-x-2 px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 disabled:bg-gray-300 disabled:cursor-not-allowed"
              >
                {executionMode === 'preview' ? <Eye className="w-4 h-4" /> : <Play className="w-4 h-4" />}
                <span>{executionMode === 'preview' ? 'Preview' : 'Run Tool'}</span>
              </button>
            </div>
          </div>
        </div>

        {executionResults && (
          <div className="bg-white rounded-lg shadow border border-gray-200 p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">Execution Results</h3>
              {executionResults.reportGenerated && (
                <button className="flex items-center space-x-1 px-3 py-1 bg-gray-100 text-gray-700 rounded text-sm hover:bg-gray-200">
                  <Download className="w-4 h-4" />
                  <span>Download Report</span>
                </button>
              )}
            </div>
            
            <div className={`${executionResults.error ? 'bg-red-50 border-red-200' : 'bg-green-50 border-green-200'} border rounded p-3 mb-4`}>
              <p className={`text-sm ${executionResults.error ? 'text-red-800' : 'text-green-800'}`}>
                {executionResults.summary}
              </p>
            </div>

            {executionResults.details && executionResults.details.length > 0 && (
              <div>
                <h4 className="font-medium text-gray-900 mb-2">
                  {tool.id === 'find-replace' ? 'URL Replacements' : 'Details'}
                  {executionResults.allFindings && executionResults.allFindings.length > 10 && 
                    ` (Showing first 10 of ${executionResults.allFindings.length})`
                  }
                </h4>
                <div className="space-y-2">
                  {executionResults.details.map((detail, index) => (
                    <div key={index} className="bg-gray-50 rounded p-3 text-sm">
                      {tool.id === 'find-replace' && detail.contentType ? (
                        <div>
                          <div className="font-medium text-gray-900">{detail.contentType} - {detail.courseName}</div>
                          <div className="text-gray-600">
                            {detail.oldUrl} → {detail.newUrl}
                          </div>
                          <div className="text-xs text-gray-500 mt-1">
                            Status: {detail.status} | Location: {detail.location}
                          </div>
                        </div>
                      ) : detail.type === 'broken' ? (
                        <div>
                          <div className="font-medium text-red-600">Broken Link</div>
                          <div className="text-gray-600">URL: {detail.url}</div>
                          <div className="text-gray-600">Location: {detail.location}</div>
                        </div>
                      ) : (
                        <div>{JSON.stringify(detail)}</div>
                      )}
                    </div>
                  ))}
                </div>
                {executionResults.totalReplacements && (
                  <div className="mt-4 text-sm text-gray-600">
                    Total replacements: {executionResults.totalReplacements} across {executionResults.coursesProcessed} course(s)
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    );
  };

  const ScriptSubmitter = () => {
    const addInput = () => {
      setSubmissionData(prev => ({
        ...prev,
        inputs: [...prev.inputs, { name: '', type: 'text', description: '', required: true }]
      }));
    };

    const updateInput = (index, field, value) => {
      setSubmissionData(prev => ({
        ...prev,
        inputs: prev.inputs.map((input, i) => 
          i === index ? { ...input, [field]: value } : input
        )
      }));
    };

    const removeInput = (index) => {
      setSubmissionData(prev => ({
        ...prev,
        inputs: prev.inputs.filter((_, i) => i !== index)
      }));
    };

    const addTag = (tag) => {
      if (tag && !submissionData.tags.includes(tag)) {
        setSubmissionData(prev => ({
          ...prev,
          tags: [...prev.tags, tag]
        }));
      }
    };

    const removeTag = (tag) => {
      setSubmissionData(prev => ({
        ...prev,
        tags: prev.tags.filter(t => t !== tag)
      }));
    };

    const availableTags = ['QA', 'Links', 'Pages', 'Dates', 'UX', 'Menus', 'Grades', 'Files', 'Export'];

    return (
      <div className="min-h-screen bg-stone-50">
        <div className="bg-white shadow-sm border-b">
          <div className="max-w-4xl mx-auto px-4 py-4 flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <button 
                onClick={() => setCurrentView('landing')}
                className="text-blue-600 hover:text-blue-800 font-medium"
              >
                ← Back to Home
              </button>
              <h1 className="text-2xl font-bold text-gray-900">Submit a Script</h1>
            </div>
          </div>
        </div>

        <div className="max-w-4xl mx-auto p-6">
          <div className="bg-white rounded-lg shadow border border-gray-200 p-6">
            <div className="mb-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-2">Script Information</h2>
              <p className="text-stone-600">Provide details about your Canvas automation script</p>
            </div>

            <div className="space-y-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Script File *
                </label>
                <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center hover:border-gray-400 transition-colors">
                  <Upload className="w-8 h-8 text-gray-400 mx-auto mb-2" />
                  <p className="text-sm text-stone-600">
                    Click to upload or drag and drop your .py or .js file
                  </p>
                  <p className="text-xs text-stone-500 mt-1">
                    Must include run() function and metadata.json
                  </p>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Tool Name *
                </label>
                <input
                  type="text"
                  value={submissionData.name}
                  onChange={(e) => setSubmissionData(prev => ({ ...prev, name: e.target.value }))}
                  placeholder="e.g., Grade Export Formatter"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-red-500 focus:border-red-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Description *
                </label>
                <textarea
                  value={submissionData.description}
                  onChange={(e) => setSubmissionData(prev => ({ ...prev, description: e.target.value }))}
                  placeholder="Describe what this tool does in simple terms..."
                  rows={3}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-red-500 focus:border-red-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  When/Why to Use This Tool *
                </label>
                <textarea
                  value={submissionData.whenToUse}
                  onChange={(e) => setSubmissionData(prev => ({ ...prev, whenToUse: e.target.value }))}
                  placeholder="Explain when LTs/LDs should use this tool and what problems it solves..."
                  rows={2}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-red-500 focus:border-red-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-3">
                  Input Parameters
                </label>
                <div className="space-y-3">
                  {submissionData.inputs.map((input, index) => (
                    <div key={index} className="border border-gray-200 rounded p-3">
                      <div className="grid grid-cols-1 md:grid-cols-4 gap-3 mb-2">
                        <input
                          type="text"
                          value={input.name}
                          onChange={(e) => updateInput(index, 'name', e.target.value)}
                          placeholder="Parameter name"
                          className="px-2 py-1 border border-gray-300 rounded text-sm"
                        />
                        <select
                          value={input.type}
                          onChange={(e) => updateInput(index, 'type', e.target.value)}
                          className="px-2 py-1 border border-gray-300 rounded text-sm"
                        >
                          <option value="text">Text</option>
                          <option value="number">Number</option>
                          <option value="boolean">Boolean</option>
                          <option value="date">Date</option>
                        </select>
                        <label className="flex items-center">
                          <input
                            type="checkbox"
                            checked={input.required}
                            onChange={(e) => updateInput(index, 'required', e.target.checked)}
                            className="rounded border-gray-300 text-red-600 focus:ring-red-500"
                          />
                          <span className="ml-1 text-sm">Required</span>
                        </label>
                        <button
                          onClick={() => removeInput(index)}
                          className="text-red-600 hover:text-red-800 text-sm"
                        >
                          Remove
                        </button>
                      </div>
                      <input
                        type="text"
                        value={input.description}
                        onChange={(e) => updateInput(index, 'description', e.target.value)}
                        placeholder="Description/help text"
                        className="w-full px-2 py-1 border border-gray-300 rounded text-sm"
                      />
                    </div>
                  ))}
                  <button
                    onClick={addInput}
                    className="text-red-600 hover:text-red-800 text-sm font-medium"
                  >
                    + Add Input Parameter
                  </button>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Tags
                </label>
                <div className="flex flex-wrap gap-2 mb-2">
                  {submissionData.tags.map(tag => (
                    <span key={tag} className="px-2 py-1 bg-purple-100 text-purple-700 text-sm rounded flex items-center">
                      {tag}
                      <button
                        onClick={() => removeTag(tag)}
                        className="ml-1 text-purple-600 hover:text-purple-800"
                      >
                        ×
                      </button>
                    </span>
                  ))}
                </div>
                <div className="flex flex-wrap gap-2">
                  {availableTags.filter(tag => !submissionData.tags.includes(tag)).map(tag => (
                    <button
                      key={tag}
                      onClick={() => addTag(tag)}
                      className="px-2 py-1 bg-stone-100 text-stone-700 text-sm rounded hover:bg-stone-200"
                    >
                      + {tag}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={submissionData.isDestructive}
                    onChange={(e) => setSubmissionData(prev => ({ ...prev, isDestructive: e.target.checked }))}
                    className="rounded border-gray-300 text-orange-600 focus:ring-orange-500"
                  />
                  <span className="ml-2 text-sm font-medium">
                    This script makes destructive changes (edits/deletes content)
                  </span>
                </label>
                {submissionData.isDestructive && (
                  <div className="mt-2 bg-orange-50 border border-orange-200 rounded p-3">
                    <p className="text-sm text-orange-800">
                      Destructive scripts require additional approval and will show warnings to users.
                    </p>
                  </div>
                )}
              </div>

              <div className="pt-4 border-t">
                <button
                  onClick={() => alert('Script submitted for review!')}
                  className="w-full px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 font-medium"
                >
                  Submit for Review
                </button>
                <p className="text-sm text-stone-500 mt-2 text-center">
                  Your script will be validated by AI and reviewed by admins before being published.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  };

  const AdminReview = () => (
    <div className="min-h-screen bg-stone-50">
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-6xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <button 
              onClick={() => setCurrentView('landing')}
              className="text-red-600 hover:text-red-800 font-medium"
            >
              ← Back to Home
            </button>
            <h1 className="text-2xl font-bold text-gray-900">Admin Review</h1>
          </div>
          <div className="text-sm text-stone-500">
            {pendingScripts.length} pending review(s)
          </div>
        </div>
      </div>

      <div className="max-w-6xl mx-auto p-6">
        <div className="mb-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-2">Pending Scripts</h2>
          <p className="text-stone-600">Review and approve submitted automation scripts</p>
        </div>

        <div className="space-y-4">
          {pendingScripts.map(script => (
            <div key={script.id} className="bg-white rounded-lg shadow border border-gray-200 p-6">
              <div className="flex items-start justify-between mb-4">
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-1">{script.name}</h3>
                  <p className="text-gray-600 mb-2">{script.description}</p>
                  <div className="flex items-center space-x-4 text-sm text-gray-500">
                    <span>By: {script.submitter}</span>
                    <span>Submitted: {script.submittedDate}</span>
                    {script.isDestructive && (
                      <span className="px-2 py-1 bg-orange-100 text-orange-700 rounded font-medium">
                        DESTRUCTIVE
                      </span>
                    )}
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  {script.aiValidation === 'passed' && (
                    <div className="flex items-center space-x-1 text-green-600">
                      <CheckCircle className="w-4 h-4" />
                      <span className="text-sm">AI Validated</span>
                    </div>
                  )}
                  {script.aiValidation === 'warning' && (
                    <div className="flex items-center space-x-1 text-orange-600">
                      <AlertTriangle className="w-4 h-4" />
                      <span className="text-sm">AI Warning</span>
                    </div>
                  )}
                </div>
              </div>

              <div className="flex flex-wrap gap-2 mb-4">
                {script.tags.map(tag => (
                  <span key={tag} className="px-2 py-1 bg-blue-100 text-blue-700 text-sm rounded">
                    {tag}
                  </span>
                ))}
              </div>

              <div className="bg-gray-50 rounded p-4 mb-4">
                <h4 className="font-medium text-gray-900 mb-2">AI Validation Results</h4>
                {script.aiValidation === 'passed' ? (
                  <div className="text-sm text-green-700">
                    ✓ No security concerns detected<br/>
                    ✓ Follows required function structure<br/>
                    ✓ No prohibited operations found<br/>
                    ✓ API usage appears safe
                  </div>
                ) : (
                  <div className="text-sm text-orange-700">
                    ⚠ Contains file system operations - requires manual review<br/>
                    ✓ No security concerns detected<br/>
                    ✓ Follows required function structure<br/>
                    ✓ API usage appears safe
                  </div>
                )}
              </div>

              <div className="bg-gray-100 rounded p-4 mb-4">
                <h4 className="font-medium text-gray-900 mb-2">Code Preview</h4>
                <pre className="text-sm text-gray-700 overflow-x-auto">
{`def run(canvas_url, api_token, course_id, inputs):
    """${script.name} - ${script.description}"""
    import requests
    import json
    
    headers = {'Authorization': f'Bearer {api_token}'}
    base_url = f"{canvas_url}/api/v1/courses/{course_id}"
    
    # Implementation details...
    return {"status": "success", "message": "Processing complete"}`}
                </pre>
              </div>

              <div className="flex space-x-3">
                <button className="flex items-center space-x-1 px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700">
                  <CheckCircle className="w-4 h-4" />
                  <span>Approve</span>
                </button>
                <button className="flex items-center space-x-1 px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700">
                  <XCircle className="w-4 h-4" />
                  <span>Reject</span>
                </button>
                <button className="flex items-center space-x-1 px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700">
                  <Settings className="w-4 h-4" />
                  <span>Request Changes</span>
                </button>
                <button className="flex items-center space-x-1 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700">
                  <ExternalLink className="w-4 h-4" />
                  <span>View Full Code</span>
                </button>
              </div>
            </div>
          ))}
        </div>

        <div className="mt-8 bg-white rounded-lg shadow border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Review Guidelines</h3>
          <div className="grid md:grid-cols-2 gap-6 text-sm">
            <div>
              <h4 className="font-medium text-gray-900 mb-2">Security Checklist</h4>
              <ul className="space-y-1 text-gray-600">
                <li>• No file system access outside sandbox</li>
                <li>• No network requests to unauthorized domains</li>
                <li>• No credential exposure or logging</li>
                <li>• Proper error handling</li>
                <li>• Input validation present</li>
              </ul>
            </div>
            <div>
              <h4 className="font-medium text-gray-900 mb-2">Quality Standards</h4>
              <ul className="space-y-1 text-gray-600">
                <li>• Clear, descriptive function names</li>
                <li>• Adequate documentation/comments</li>
                <li>• Follows Canvas API best practices</li>
                <li>• Handles edge cases appropriately</li>
                <li>• Returns structured results</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );

  return (
    <div className="font-sans">
      {currentView === 'landing' && <LandingPage />}
      {currentView === 'runner' && <ToolRunner />}
      {currentView === 'submitter' && <ScriptSubmitter />}
      {currentView === 'admin' && <AdminReview />}
    </div>
  );
};

export default CanvasOps;