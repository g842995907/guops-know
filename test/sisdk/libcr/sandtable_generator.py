 # -*- coding: UTF-8 -*-


import json
from sisdk.libcr.proto3.cr_sandtable_pb2 import sandtable_entity,sandtable_task,sandtable_building
from sisdk.messages import wrap_message

# 定义建筑物这个类

class Buildings(object):
	def __init__(self, building_id,label,pos_x,pos_z):
		self.id = building_id
		self.label = label
		self.pos_x = pos_x
		self.pos_z = pos_z


	def to_dict(self):
		dict_bd = {"id":self.id,
					"pos_x":self.pos_x,
					"pos_z":self.pos_z,
				   	"label":self.label}
		return dict_bd


# 定义任务这个类

class Tasks(object):
	def __init__(self, state,id,label,building_id,pos_y,radius,score):
		self.id =id
		self.state = state
		self.label = label
		self.building_id = building_id
		self.pos_y = pos_y
		self.radius = radius
		self.score = score

	def to_dict(self):
		"""
		序列化为字典
		"""
		dict_task = {"state":self.state,
						"id":self.id,
						"label":self.label,
						"building_id":self.building_id,
						"pos_y":self.pos_y,
						"radius":self.radius,
						"score":self.score}

		return dict_task


# 定义Sandtable_Generator这个类

class Sandtable_Generator(object):
	def __init__(self):
		self.buildings = []
		self.tasks = []


	def add_buildings(self,buildings_obj):
		self.buildings.append(buildings_obj)


	def add_tasks(self,tasks_obj):
		self.tasks.append(tasks_obj)

	def to_dict(self):
		dict_sg = {"buildings":[b.to_dict() for b in self.buildings],
					"tasks":[t.to_dict() for t in self.tasks]}
		return dict_sg


	def to_json(self):
		"""
        序列化为json字符串
        """
		return json.dumps(self.to_dict(),indent = 4)  #,indent = 4

	def get_buildings_binary(self):
		buildings_bin = []
		for bs in self.buildings:
			dict_data = bs.to_dict()
			bs_bin = sandtable_building(**dict_data)
			buildings_bin.append(bs_bin)
		return buildings_bin

	def get_tasks_binary(self):
		tasks_bin = []
		for tb in self.tasks:
			dict_data = tb.to_dict()
			tb_bin = sandtable_task(**dict_data)
			tasks_bin.append(tb_bin)
		return tasks_bin

	def to_binary(self):
		b_buildings = self.get_buildings_binary()
		b_tasks = self.get_tasks_binary()
		b_init = sandtable_entity(buildings = b_buildings, tasks = b_tasks)
		return wrap_message(b_init)


	def to_json(self):
		pass

	# def cr_sandtable_entity(self):
	# 	return self.to_binary()

"""
	def from_json(self, json_string):
		self.buildings = []
		self.tasks = []
		dict_sg = json.loads(json_string)

		for bd in dict_sg['buildings']:
			bd_obj = Buildings(bd['buildings_id'], bd['pos_x'], bd['pos_y'])
			self.buildings.append(bd_obj)

		for ts in dict_sg['tasks']:
			ts_obj = Tasks(ts['state'], ts['id'], ts['label'], ts['buildings_id'], ts['pos_y'], ts['radius'],
						   ts['score'])
			self.tasks.append(ts_obj)
"""


"""
if __name__ == '__main__':
	 sg = Sandtable_Generator()
	 bd1 = Buildings("282882", 100, 200,"Test_team")
	 sg.add_buildings(bd1)
	 tk = Tasks("完成", "t-122", "攻防", "t-1",300, 100, 500)
	 sg.add_tasks(tk)


"""
