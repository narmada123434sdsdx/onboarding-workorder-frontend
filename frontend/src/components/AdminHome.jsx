import React, { useState } from 'react';
import { 
  Briefcase, 
  CheckCircle, 
  Clock, 
  AlertCircle,
  DollarSign,
  Users,
  Building2,
  User,
  TrendingUp,
  Activity,
  Calendar,
  FileText
} from 'lucide-react';
import './css/AdminHome.css';

function AdminHome(){
  // Sample data - replace with your API calls
  const [dashboardData] = useState({
    workOrders: {
      total: 1248,
      active: 342,
      completed: 856,
      pending: 50,
      trend: '+12%'
    },
    standardRate: {
      hourly: 85,
      overtime: 127.5,
      weekend: 170,
      emergency: 212.5
    },
    users: {
      companyUsers: 45,
      individualUsers: 892,
      newThisMonth: 23,
      activeToday: 156
    },
    revenue: {
      thisMonth: 125840,
      lastMonth: 108230,
      growth: '+16.3%'
    },
    recentActivity: [
      { id: 1, type: 'workorder', desc: 'New work order #WO-1249 created', time: '5 min ago' },
      { id: 2, type: 'user', desc: 'New company user registered', time: '12 min ago' },
      { id: 3, type: 'complete', desc: 'Work order #WO-1245 completed', time: '1 hour ago' },
      { id: 4, type: 'rate', desc: 'Standard rate updated', time: '2 hours ago' }
    ]
  });

  const StatCard = ({ title, value, icon: Icon, trend, color, subtitle }) => (
    <div className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <p className="text-gray-500 text-sm font-medium mb-1">{title}</p>
          <h3 className="text-3xl font-bold text-gray-800 mb-2">{value}</h3>
          {subtitle && <p className="text-sm text-gray-600">{subtitle}</p>}
          {trend && (
            <span className={`inline-flex items-center text-sm font-medium mt-2 ${
              trend.startsWith('+') ? 'text-green-600' : 'text-red-600'
            }`}>
              <TrendingUp className="w-4 h-4 mr-1" />
              {trend} from last month
            </span>
          )}
        </div>
        <div className={`p-3 rounded-lg ${color}`}>
          <Icon className="w-6 h-6 text-white" />
        </div>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Admin Dashboard</h1>
          <p className="text-gray-600">Welcome back! Here's your business overview</p>
        </div>

        {/* Work Orders Section */}
        <div className="mb-8">
          <h2 className="text-xl font-semibold text-gray-800 mb-4 flex items-center">
            <Briefcase className="w-5 h-5 mr-2" />
            Work Orders Summary
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <StatCard
              title="Total Work Orders"
              value={dashboardData.workOrders.total.toLocaleString()}
              icon={FileText}
              trend={dashboardData.workOrders.trend}
              color="bg-blue-500"
            />
            <StatCard
              title="Active Work Orders"
              value={dashboardData.workOrders.active}
              icon={Activity}
              color="bg-green-500"
              subtitle="Currently in progress"
            />
            <StatCard
              title="Completed"
              value={dashboardData.workOrders.completed}
              icon={CheckCircle}
              color="bg-purple-500"
              subtitle="Successfully finished"
            />
            <StatCard
              title="Pending"
              value={dashboardData.workOrders.pending}
              icon={Clock}
              color="bg-orange-500"
              subtitle="Awaiting action"
            />
          </div>
        </div>

        {/* Standard Rate Section */}
        <div className="mb-8">
          <h2 className="text-xl font-semibold text-gray-800 mb-4 flex items-center">
            <DollarSign className="w-5 h-5 mr-2" />
            Standard Rates
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <div className="bg-white rounded-lg shadow-md p-6">
              <div className="flex items-center justify-between mb-2">
                <p className="text-gray-500 text-sm font-medium">Hourly Rate</p>
                <Calendar className="w-5 h-5 text-blue-500" />
              </div>
              <h3 className="text-2xl font-bold text-gray-800">
                ${dashboardData.standardRate.hourly}
              </h3>
              <p className="text-sm text-gray-600 mt-1">Standard hours</p>
            </div>
            <div className="bg-white rounded-lg shadow-md p-6">
              <div className="flex items-center justify-between mb-2">
                <p className="text-gray-500 text-sm font-medium">Overtime Rate</p>
                <Clock className="w-5 h-5 text-orange-500" />
              </div>
              <h3 className="text-2xl font-bold text-gray-800">
                ${dashboardData.standardRate.overtime}
              </h3>
              <p className="text-sm text-gray-600 mt-1">1.5x standard</p>
            </div>
            <div className="bg-white rounded-lg shadow-md p-6">
              <div className="flex items-center justify-between mb-2">
                <p className="text-gray-500 text-sm font-medium">Weekend Rate</p>
                <Calendar className="w-5 h-5 text-purple-500" />
              </div>
              <h3 className="text-2xl font-bold text-gray-800">
                ${dashboardData.standardRate.weekend}
              </h3>
              <p className="text-sm text-gray-600 mt-1">2x standard</p>
            </div>
            <div className="bg-white rounded-lg shadow-md p-6">
              <div className="flex items-center justify-between mb-2">
                <p className="text-gray-500 text-sm font-medium">Emergency Rate</p>
                <AlertCircle className="w-5 h-5 text-red-500" />
              </div>
              <h3 className="text-2xl font-bold text-gray-800">
                ${dashboardData.standardRate.emergency}
              </h3>
              <p className="text-sm text-gray-600 mt-1">2.5x standard</p>
            </div>
          </div>
        </div>

        {/* Users Section */}
        <div className="mb-8">
          <h2 className="text-xl font-semibold text-gray-800 mb-4 flex items-center">
            <Users className="w-5 h-5 mr-2" />
            Users Overview
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <StatCard
              title="Company Users"
              value={dashboardData.users.companyUsers}
              icon={Building2}
              color="bg-indigo-500"
              subtitle="Business accounts"
            />
            <StatCard
              title="Individual Users"
              value={dashboardData.users.individualUsers}
              icon={User}
              color="bg-cyan-500"
              subtitle="Personal accounts"
            />
            <StatCard
              title="New This Month"
              value={dashboardData.users.newThisMonth}
              icon={TrendingUp}
              color="bg-green-500"
              subtitle="Recent sign-ups"
            />
            <StatCard
              title="Active Today"
              value={dashboardData.users.activeToday}
              icon={Activity}
              color="bg-blue-500"
              subtitle="Currently online"
            />
          </div>
        </div>

        {/* Revenue and Activity Section */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Revenue Card */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-xl font-semibold text-gray-800 mb-4 flex items-center">
              <DollarSign className="w-5 h-5 mr-2" />
              Revenue Overview
            </h2>
            <div className="space-y-4">
              <div className="flex items-center justify-between p-4 bg-green-50 rounded-lg">
                <div>
                  <p className="text-sm text-gray-600 mb-1">This Month</p>
                  <p className="text-2xl font-bold text-gray-800">
                    ${dashboardData.revenue.thisMonth.toLocaleString()}
                  </p>
                </div>
                <span className="text-green-600 font-semibold text-lg">
                  {dashboardData.revenue.growth}
                </span>
              </div>
              <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                <div>
                  <p className="text-sm text-gray-600 mb-1">Last Month</p>
                  <p className="text-2xl font-bold text-gray-800">
                    ${dashboardData.revenue.lastMonth.toLocaleString()}
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Recent Activity Card */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-xl font-semibold text-gray-800 mb-4 flex items-center">
              <Activity className="w-5 h-5 mr-2" />
              Recent Activity
            </h2>
            <div className="space-y-3">
              {dashboardData.recentActivity.map((activity) => (
                <div key={activity.id} className="flex items-start p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors">
                  <div className={`p-2 rounded-full mr-3 ${
                    activity.type === 'workorder' ? 'bg-blue-100' :
                    activity.type === 'user' ? 'bg-green-100' :
                    activity.type === 'complete' ? 'bg-purple-100' :
                    'bg-orange-100'
                  }`}>
                    {activity.type === 'workorder' && <FileText className="w-4 h-4 text-blue-600" />}
                    {activity.type === 'user' && <Users className="w-4 h-4 text-green-600" />}
                    {activity.type === 'complete' && <CheckCircle className="w-4 h-4 text-purple-600" />}
                    {activity.type === 'rate' && <DollarSign className="w-4 h-4 text-orange-600" />}
                  </div>
                  <div className="flex-1">
                    <p className="text-sm font-medium text-gray-800">{activity.desc}</p>
                    <p className="text-xs text-gray-500 mt-1">{activity.time}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AdminHome;